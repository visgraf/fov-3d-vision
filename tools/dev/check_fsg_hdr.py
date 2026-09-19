"""FSG1c software tests and deliberately failing controls; no Blender required.

 python tools/dev/check_fsg_hdr.py --self-test --report OUT.json
 python tools/dev/check_fsg_hdr.py --negative encoder  # MUST exit 1
 python tools/dev/check_fsg_hdr.py --negative replay   # MUST exit 1
 python tools/dev/check_fsg_hdr.py --negative geometry # MUST exit 1
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import numpy as np
import cv2
TOOLS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TOOLS), str(TOOLS / 'dev')]
import fsg_stereo as s
import fsg_stereo_hdr as h
import fsg_hdr_compare as c
import fsg_render as r
import fsg_evaluate as e
import fsg_geometry as g
from fake_blender_fsg import SyntheticBackend


def require(ok, message='assertion'):
    if not ok:
        raise AssertionError(message)


def raises(kind, fn):
    try:
        fn()
    except kind:
        return
    raise AssertionError(f'expected {kind.__name__}')


def encoding_control(encoder):
    values = encoder(np.array([1., 2., 4.]))
    require(np.all(np.diff(values.astype(float)) > 0), 'distinct HDR inputs collapsed; pre-quantization clipping returned')


def geometry_control():
    truth = {'position_h': np.array([[0., 0., -2.]] * 200),
             'range_m': np.full(200, 2.), 'normal_h': np.array([[0., 0., 1.]] * 200)}
    mask = np.ones(200, bool)
    metrics = e.describe_errors(1.2 * truth['position_h'], truth, np.zeros(3), mask, mask)
    return e.gate(metrics)


class BrightBackend(SyntheticBackend):
    """Software stress only: all raw RGB > 1, including the tilted fixture.
    Fixed affine remapping of a known analytic texture, identical for both eyes.
    Neither a new Blender fixture nor an observation in the actual experiment.
    """
    def render_eye(self, *args):
        rgb, seconds = super().render_eye(*args)
        return 1.2 + 2. * rgb, seconds


def self_test() -> dict:
    checks = []; details = io.StringIO(); start = time.perf_counter()
    def check(name, fn):
        try:
            fn(); checks.append({'name': name, 'pass': True}); print('[fsg-hdr-check] PASS', name)
        except Exception as exc:
            checks.append({'name': name, 'pass': False, 'error': repr(exc)}); print('[fsg-hdr-check] FAIL', name, repr(exc))
    check('frozen legacy source hashes', c.a.check_sources)
    check('kernel differs only at declared encoder call', h.check_kernel_equivalence)
    check('HDR distinctions survive fixed mapping', lambda: encoding_control(h.hdr_to_u8))
    check('legacy clipping trips encoding control', lambda: raises(AssertionError, lambda: encoding_control(s.linear_to_u8)))
    check('mapping known values', lambda: require(np.array_equal(h.hdr_to_u8(np.array([0., 1., 2., 4.])), [0, 188, 213, 231])))
    check('finite mapping is monotone and uint8', lambda: require(
        h.hdr_to_u8(np.geomspace(1e-9, 1e9, 10000)).dtype == np.uint8 and
        np.all(np.diff(h.hdr_to_u8(np.geomspace(1e-9, 1e9, 10000)).astype(int)) >= 0)))
    check('negative floor and extreme HDR finite', lambda: require(np.array_equal(h.hdr_to_u8(np.array([-2., 0., 1e308])), [0, 0, 255])))
    check('nonfinite RGB rejected', lambda: raises(ValueError, lambda: h.hdr_to_u8(np.array([np.nan]))))
    def pointwise():
        left = np.array([[[1., 2., 4.]]]); other = np.concatenate([left, np.full_like(left, 1000.)], axis=1)
        require(np.array_equal(h.hdr_to_u8(left), h.hdr_to_u8(other)[:, :1]), 'encoding depends on image statistics')
        require(np.array_equal(h.hdr_to_u8(left), h.hdr_to_u8(left.copy())), 'eye-dependent encoding')
    check('pointwise encoding has no per-image or per-eye adaptation', pointwise)
    check('depth-scale corruption fails original gate', lambda: require(bool(geometry_control())))
    with tempfile.TemporaryDirectory(prefix='fsg1c-check-') as temp:
        root = Path(temp); run = root / 'bright-small'
        args = r.parse_args(['--out', str(run), '--profile', 'small']); args.spp = 64
        with contextlib.redirect_stdout(details):
            r.acquire(args, BrightBackend())
            for case in ('fronto', 'tilted', 'step'):
                s.process_pair(run / case)
        folder = run / 'tilted'; calibration, obs = h.read_observation(folder)
        baseline, _ = s.compute(calibration, obs)
        candidate, _ = h.compute_candidate(calibration, obs)
        mesh = c.a.load_npz(folder / 'evaluation_only' / 'mesh.npz')
        ev, ctx = c.candidate_evaluation(calibration, candidate, mesh, False, True)
        check('bright tilted fixture really defeats old clipped encoding', lambda: require(not np.any(baseline['valid'])))
        check('bright tilted candidate passes unchanged numerical gate', lambda: require(ev['checks_pass'], str(ev['fails'])))
        check('candidate points finite and in front', lambda: require(
            np.isfinite(candidate['xyz_h'][candidate['valid']]).all() and np.all(candidate['z_rect_m'][candidate['valid']] > 0)))
        check('texture veto retained on uniformly dark pair', lambda: _blank(calibration, obs, .4))
        check('texture veto retained on uniformly bright pair', lambda: _blank(calibration, obs, 4.))
        check('depth in observation rejected', lambda: raises(ValueError, lambda: h.compute_candidate(calibration, dict(obs, depth=np.ones((1,))))))
        check('candidate does not mutate legacy globals or results', lambda: c.a.assert_replay(baseline, s.compute(calibration, obs)[0]))
        def replay_negative():
            altered = {k: v.copy() for k, v in baseline.items()}; altered['valid'][0, 0] ^= True
            raises(ValueError, lambda: c.a.assert_replay(baseline, altered))
        check('altered validity fails replay', replay_negative)
        def no_truth():
            truth = folder / 'evaluation_only'; hidden = folder / 'truth_hidden'
            truth.rename(hidden)
            try:
                fresh, _ = h.reconstruct_pair(folder, root / 'without-truth')
                c.a.assert_replay(candidate, fresh)
            finally:
                hidden.rename(truth)
        check('candidate reconstruction is identical with truth removed', no_truth)
        check('refuses output under input record', lambda: raises(ValueError, lambda: h.reconstruct_pair(folder, folder / 'illegal')))
        check('refuses to overwrite candidate output', lambda: raises(FileExistsError, lambda: h.reconstruct_pair(folder, root / 'without-truth')))
        before = c.snapshot([run])
        with contextlib.redirect_stdout(details):
            report = c.compare([run], root / 'compare', allow_synthetic=True)
        check('full comparison orchestration all bright fixture gates', lambda: require(report['all_requested_candidate_gates_pass']))
        check('all source bytes preserved', lambda: require(before == c.snapshot([run])))
        check('synthetic candidate cannot promote milestone', lambda: require(
            not report['full_profile_milestone_pass'] and not report['fusion_authorized'] and
            report['runs'][0]['status'] == 'SYNTHETIC_CANDIDATE_PASS_NOT_A_RENDER_RESULT'))
        check('comparison reports zero new camera samples', lambda: require(report['new_primary_samples'] == 0))
        check('all baseline replays exact', lambda: require(all(v['legacy_replay_exact'] for v in report['runs'][0]['cases'].values())))
        check('produces visible candidate comparison', lambda: require((root / 'compare' / run.name / 'step' / 'comparison.png').is_file()))
        def all_partitions():
            for case in report['runs'][0]['cases'].values():
                for item in case['paired'].values():
                    require(sum(item['mask_counts'].values()) == item['reference_pixels'])
        check('paired acceptance partitions preserve fixed denominators', all_partitions)
        check('empty half-occlusion reference remains NOT_EXERCISED', lambda: require(
            all(v['candidate']['reference_status']['singly_visible'] == 'NOT_EXERCISED' for v in report['runs'][0]['cases'].values())))
        with contextlib.redirect_stdout(details):
            check('production comparison refuses synthetic provenance', lambda: raises(ValueError, lambda: c.compare([run], root / 'forbidden')))
        check('comparison refuses reused output', lambda: raises(ValueError, lambda: c.compare([run], root / 'compare', True)))
        check('comparison refuses nested output', lambda: raises(ValueError, lambda: c.compare([run], run / 'nested', True)))
        calfile = folder / 'calibration.json'; contents = calfile.read_text(); calfile.write_text(contents + ' ')
        with contextlib.redirect_stdout(details):
            check('stale input fingerprint stops comparison', lambda: raises(ValueError, lambda: c.compare([run], root / 'stale', True)))
        calfile.write_text(contents)
        check('all frozen sources still untouched', c.a.check_sources)
    result = {'schema': 'FSG1c-software-checks-v1', 'checks': checks,
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'seconds': time.perf_counter() - start, 'blender_executed': False,
              'python': sys.version, 'numpy': np.__version__, 'opencv': cv2.__version__,
              'details': details.getvalue()}
    print(f"[fsg-hdr-check] SUMMARY passed={result['passed']} failed={result['failed']} "
          f"seconds={result['seconds']:.3f} blender_executed=False")
    return result


def _blank(calibration: dict, obs: dict, value: float):
    changed = {k: v.copy() for k, v in obs.items()}
    changed['rgb_L'][:] = value; changed['rgb_R'][:] = value
    result, _ = h.compute_candidate(calibration, changed)
    require(not np.any(result['valid']), f'blank {value} generated geometry')


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--self-test', action='store_true')
    p.add_argument('--negative', choices=('encoder', 'replay', 'geometry')); p.add_argument('--report', type=Path)
    args = p.parse_args()
    if args.negative == 'encoder':
        encoding_control(s.linear_to_u8)
    elif args.negative == 'replay':
        c.a.assert_replay({'valid': np.array([True])}, {'valid': np.array([False])})
    elif args.negative == 'geometry':
        failures = geometry_control()
        require(not failures, 'deliberate 20-percent range error: ' + '; '.join(failures))
    elif args.self_test:
        report = self_test()
        if args.report:
            g.json_write(args.report, report)
        raise SystemExit(1 if report['failed'] else 0)
    else:
        p.error('choose --self-test or --negative')
    raise SystemExit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'[fsg-hdr-check] FAIL {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
