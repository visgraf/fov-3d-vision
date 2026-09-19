"""Checks for the additive coverage audit; no Blender or workstation assets.

  python tools/dev/check_fsg_coverage_audit.py --self-test
  python tools/dev/check_fsg_coverage_audit.py --negative replay     # exit 1
  python tools/dev/check_fsg_coverage_audit.py --negative partition  # exit 1
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

import cv2
import numpy as np

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS)); sys.path.insert(0, str(TOOLS / 'dev'))
import fsg_coverage_audit as a
import fsg_geometry as g
import fsg_stereo as s
import fsg_render as render
import fsg_evaluate as evaluate
from fake_blender_fsg import SyntheticBackend


def rejects(fn) -> None:
    try: fn()
    except (ValueError, FileExistsError): return
    raise AssertionError('operation should have rejected this input')


def need(condition, text='assertion failed'):
    if not condition: raise AssertionError(text)


def negative(kind: str) -> None:
    if kind == 'replay':
        a.assert_replay({'valid': np.array([True])}, {'valid': np.array([False])})
    else:
        ref = np.ones(3, bool)
        a.check_partition({'accepted': ref, 'texture_only_veto': ref,
                           'other_veto': np.zeros(3, bool)}, ref)


def self_test(report_path: Path | None) -> dict:
    start = time.perf_counter(); checks = []; detail = io.StringIO()
    def check(name, fn):
        try:
            fn(); checks.append({'name': name, 'pass': True})
            print('[fsg-audit-check] PASS', name)
        except Exception as exc:
            checks.append({'name': name, 'pass': False, 'error': repr(exc)})
            print('[fsg-audit-check] FAIL', name, repr(exc))
    check('frozen sources match handoff', a.check_sources)
    masks = {'texture': np.array([True, False, False, True]),
             'lr': np.array([True, True, False, False])}
    groups = a.partition(masks)
    check('exclusive rejection partition', lambda: a.check_partition(groups, np.ones(4, bool)))
    check('texture failure is not necessarily sole veto', lambda: need(
        groups['texture_only_veto'].sum() == 1 and (~masks['texture']).sum() == 2))
    check('deliberate replay mutation is detected', lambda: rejects(lambda: negative('replay')))
    check('deliberate partition overlap is detected', lambda: rejects(lambda: negative('partition')))
    check('empty statistics are null not NaN', lambda: need(a.distribution(np.array([]))['quantiles'] is None))
    check('known statistics', lambda: need(a.distribution(np.array([0., 1., 2.]))['quantiles']['median'] == 1.))
    check('fixed denominator with no accepted points is zero coverage', lambda: need(
        evaluate.describe_errors(np.zeros((2, 2, 3)), {}, np.zeros(3), np.zeros((2, 2), bool),
                                 np.ones((2, 2), bool))['coverage'] == 0.))
    check('altered official metric detected', lambda: rejects(lambda: a.verify_official_metrics(
        {'reference_pixels': 100, 'accepted_pixels': 50, 'coverage': .5,
         'median_relative_range_error': .01, 'p95_relative_range_error': .02},
        {'reference_pixels': 100, 'accepted_pixels': 90, 'coverage': .9,
         'median_relative_range_error': .01, 'p95_relative_range_error': .02})))
    for profile, kernel in [('small', 5), ('full', 9)]:
        c = g.make_calibration(profile); r = s.rectification(c)
        n = c['image_size_wh'][0]
        # Horizontal variation below one U8 display quantization bin.
        v, u = np.mgrid[:n, :n]
        rgb = np.repeat((.4 + (u[..., None] - n / 2) * 1e-6), 3, axis=2).astype(np.float32)
        ids = np.ones((n, n), np.int32)
        fields, settings = a.diagnostic_fields(c, r, rgb, ids)
        check(profile + ' angle-matched kernel', lambda settings=settings, kernel=kernel: need(settings['angle_matched_kernel'] == kernel))
        centre = n // 2
        check(profile + ' U8 zero is not necessarily float zero', lambda fields=fields, centre=centre: need(
            fields['std5_u8_float64_arithmetic'][centre, centre] == 0 and
            fields['std5_float_display'][centre, centre] > 0))
    c = g.make_calibration('small'); n = c['image_size_wh'][0]
    v, u = np.mgrid[:n, :n]
    rgb = np.repeat((.2 + .6 * v[..., None] / n), 3, axis=2).astype(np.float32)
    fields, _ = a.diagnostic_fields(c, s.rectification(c), rgb, np.ones((n, n), np.int32))
    check('horizontal information distinct from total contrast', lambda: need(
        np.max(fields['gradient_x_rms_linear']) == 0 and fields['gradient_y_rms_linear'][100, 100] > 0))
    hdr = np.repeat((1.2 + .3 * u[..., None] / n), 3, axis=2).astype(np.float32)
    hdr_fields, _ = a.diagnostic_fields(c, s.rectification(c), hdr, np.ones((n, n), np.int32))
    check('display clipping distinguished from flat linear RGB', lambda: need(
        hdr_fields['std5_u8_float64_arithmetic'][100, 100] == 0 and
        hdr_fields['std5_unclipped_linear_luminance'][100, 100] > 0 and
        bool(hdr_fields['all_rgb_high_clipped'][100, 100])))
    with tempfile.TemporaryDirectory(prefix='fsg-audit-tests-') as tmp:
        root = Path(tmp); run = root / 'small-synthetic'
        args = render.parse_args(['--out', str(run), '--profile', 'small']); args.spp = 64
        with contextlib.redirect_stdout(detail):
            render.acquire(args, SyntheticBackend())
            for name in ('fronto', 'tilted', 'step'): s.process_pair(run / name)
            evaluate.evaluate_run(run, allow_synthetic=True)
        before = a.snapshot([run])
        output = root / 'audit'
        try:
            with contextlib.redirect_stdout(detail): report = a.audit([run], output, allow_synthetic=True)
            check('three-case saved-record integration', lambda: need(len(report['runs'][0]['cases']) == 3))
            check('all records unchanged', lambda: need(before == a.snapshot([run]) and report['inputs_unchanged']))
            check('audit never approves a milestone', lambda: need(report['status'] == 'AUDIT_COMPLETE_NOT_A_MILESTONE' and not report['fsg1_authorized_pass']))
            check('visual artifact for every case', lambda: need(all(
                (output / run.name / name / 'diagnostic.png').is_file() for name in ('fronto', 'tilted', 'step'))))
            check('no production reconstruction or evaluator output', lambda: need(
                not list(output.rglob('result.npz')) and not list(output.rglob('evaluation.json')) and not list(output.rglob('*.ply'))))
            check('refuses existing output', lambda: rejects(lambda: a.audit([run], output, True)))
        except Exception as exc:
            check('three-case saved-record integration', lambda exc=exc: need(False, repr(exc)))
        check('refuses output under input', lambda: rejects(lambda: a.validate_paths([run], run / 'audit')))
        check('refuses synthetic as a real measurement', lambda: rejects(lambda: a.audit([run], root / 'fake-real')))
        folder = run / 'fronto'
        c = json.loads((folder / 'calibration.json').read_text())
        obs = a.load_npz(folder / 'observation.npz'); stored = a.load_npz(folder / 'stereo' / 'result.npz')
        def no_truth_replay():
            source = folder / 'evaluation_only'; hidden = folder / 'hidden_truth'
            source.rename(hidden)
            try:
                trace = a.trace_rgb(c, obs, stored)
                need(np.array_equal(trace['fresh']['valid'], stored['valid']))
            finally: hidden.rename(source)
        check('RGB-only replay works with truth directory absent', no_truth_replay)
        def blank_test():
            blank = {k: v.copy() for k, v in obs.items()}
            blank['rgb_L'][:] = .4; blank['rgb_R'][:] = .4
            b, _ = s.compute(c, blank); trace = a.trace_rgb(c, blank, b)
            need(not trace['groups']['accepted'].any())
            need(not trace['groups']['texture_only_veto'].any(), 'blank invalid disparity must not become recoverable')
        check('blank images stay rejected for other reasons too', blank_test)
        def stale_inputs():
            path = folder / 'calibration.json'; original = path.read_bytes()
            path.write_bytes(original + b' ')
            try: rejects(lambda: a.audit([run], root / 'stale-audit', True))
            finally: path.write_bytes(original)
        check('stale calibration hash is detected', stale_inputs)
        def corrupt_saved_record():
            path = folder / 'stereo' / 'result.npz'; original = path.read_bytes()
            altered = {k: v.copy() for k, v in stored.items()}; altered['disparity_px'][0, 0] += 1
            np.savez_compressed(path, **altered)
            try: rejects(lambda: a.audit([run], root / 'corrupt-audit', True))
            finally: path.write_bytes(original)
        check('actual saved-disparity mutation stops audit', corrupt_saved_record)
        source_copy = root / 'sources'; source_copy.mkdir()
        for name in a.FROZEN_SHA256: shutil.copy2(TOOLS / name, source_copy / name)
        with (source_copy / 'fsg_stereo.py').open('ab') as stream: stream.write(b'\n# deliberate mutation\n')
        check('source mutation guard can fail', lambda: rejects(lambda: a.check_sources(source_copy)))
        check('all test mutations restored', lambda: need(before == a.snapshot([run])))
    result = {'schema': 'FSG1-coverage-audit-checks-v1', 'checks': checks,
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'seconds': time.perf_counter() - start, 'blender_executed': False,
              'numpy': np.__version__, 'opencv': cv2.__version__}
    print(f"[fsg-audit-check] SUMMARY passed={result['passed']} failed={result['failed']} "
          f"seconds={result['seconds']:.3f} blender_executed=False")
    if report_path: g.json_write(report_path, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test', action='store_true')
    p.add_argument('--negative', choices=('replay', 'partition'))
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    if args.negative:
        negative(args.negative)
        raise RuntimeError('negative unexpectedly did not fail')
    if not args.self_test: p.error('select --self-test or --negative')
    raise SystemExit(1 if self_test(args.report)['failed'] else 0)


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'[fsg-audit-check] FAIL {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
