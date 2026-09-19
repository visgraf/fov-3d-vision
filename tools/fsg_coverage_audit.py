"""Read-only FSG1 coverage audit. Diagnostic output can never approve FSG1.

Reads existing run records, replays the FROZEN estimator, and reconstructs its
acceptance conjunction. Ground truth is used only after the RGB-only replay, to
score hypotheses the original estimator rejected. No new reconstruction is saved.

  python tools/fsg_coverage_audit.py RUN [RUN ...] --out NEW_AUDIT_DIRECTORY
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from functools import reduce

import cv2
import numpy as np
from PIL import Image, ImageDraw

import fsg_geometry as g
import fsg_stereo as s
import fsg_evaluate as e

FROZEN_SHA256 = {
    'fsg_geometry.py': 'd9537d8ebc23b60c30e957b484d7353c20ca751f2281729d4ea941e2aacecd5d',
    'fsg_scene.py': '1f410577c1103e0197a63a77eef3f47e640807b833876dfde296014fc8b3b134',
    'fsg_stereo.py': 'faebf0f1b3acbfde60b08830a57213bf29c708c3aa274e493ade0042eb0545e9',
    'fsg_evaluate.py': 'a5134b8d8537714d3b9cb074ec65e3bb83dc574827db42359ad27e14c1626da3',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_sources(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parent
    got = {name: s.sha256(root / name) for name in FROZEN_SHA256}
    require(got == FROZEN_SHA256, 'frozen source fingerprint mismatch; stop, do not relax this guard')
    return got


def load_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as f:
        return {k: f[k] for k in f.files}


def assert_replay(stored: dict, replay: dict) -> None:
    require(stored.keys() == replay.keys(), 'replay result keys differ')
    for key in stored:
        require(np.array_equal(stored[key], replay[key], equal_nan=True),
                f'replay mismatch in {key}; no counterfactual analysis authorized')


def intersect(masks: dict) -> np.ndarray:
    require(bool(masks), 'empty mask conjunction')
    return reduce(np.logical_and, masks.values())


def partition(masks: dict) -> dict:
    """Exclusive partition; a failed texture test need not be the sole veto."""
    base = intersect({k: v for k, v in masks.items() if k != 'texture'})
    return {'accepted': base & masks['texture'],
            'texture_only_veto': base & ~masks['texture'],
            'other_veto': ~base}


def check_partition(groups: dict, reference: np.ndarray) -> None:
    require(set(groups) == {'accepted', 'texture_only_veto', 'other_veto'}, 'wrong partition keys')
    n = sum(v.astype(np.uint8) for v in groups.values())
    require(bool(np.all(n[reference] == 1)), 'partition overlaps or misses reference pixels')


def distribution(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=float).ravel()
    a = a[np.isfinite(a)]
    if not a.size:
        return {'n': 0, 'quantiles': None, 'zero_fraction': None}
    return {'n': int(a.size), 'quantiles': dict(zip(
        ['min', 'p05', 'p25', 'median', 'p75', 'p95', 'max'],
        map(float, np.quantile(a, [0, .05, .25, .5, .75, .95, 1])))),
        'zero_fraction': float(np.mean(a == 0))}


def local_std(a: np.ndarray, size: int) -> np.ndarray:
    # Float64 diagnostic avoids cancellation in E[x^2]-E[x]^2. The original
    # float32 production score is retained independently and reproduced exactly.
    a = np.asarray(a, np.float64)
    mean = lambda x: cv2.boxFilter(x, -1, (size, size), borderType=cv2.BORDER_DEFAULT)
    return np.sqrt(np.maximum(mean(a * a) - mean(a) ** 2, 0.))


def diagnostic_fields(c: dict, r: dict, rgb: np.ndarray, ids: np.ndarray) -> tuple[dict, dict]:
    gray8 = cv2.cvtColor(s.linear_to_u8(rgb), cv2.COLOR_RGB2GRAY)
    a = np.clip(rgb.astype(np.float64), 0., 1.)
    a = np.where(a <= .0031308, 12.92 * a, 1.055 * a ** (1 / 2.4) - .055)
    grayf = cv2.cvtColor((255 * a).astype(np.float32), cv2.COLOR_RGB2GRAY)
    cs = g.make_calibration('small', *c['gaze_yaw_pitch_deg'],
                            c['prescribed_vergence_distance_m'], c['ipd_m'],
                            np.asarray(c['head_R_wh']), np.asarray(c['head_origin_w_m']))
    fsmall = float(s.rectification(cs)['P1'][0, 0])
    focal = float(r['P1'][0, 0])
    # Preserve the +/-2-sample centre span of the original SMALL window.
    # The discrete kernel is approximately angle-matched, not an exact area match.
    radius = max(1, int(round(2 * focal / fsmall)))
    k = 2 * radius + 1
    luminance = rgb.astype(np.float32) @ np.array([.2126, .7152, .0722], np.float32)
    gx = cv2.Sobel(luminance, cv2.CV_32F, 1, 0, ksize=3, scale=1 / 8)
    gy = cv2.Sobel(luminance, cv2.CV_32F, 0, 1, ksize=3, scale=1 / 8)
    rms = lambda v: np.sqrt(np.maximum(cv2.boxFilter(v * v, -1, (5, 5)), 0.))
    fields = {'std5_u8_float64_arithmetic': local_std(gray8, 5),
              'std5_float_display': local_std(grayf, 5),
              'std_angle_matched_u8': local_std(gray8, k),
              'gradient_x_rms_linear': rms(gx), 'gradient_y_rms_linear': rms(gy),
              'std5_unclipped_linear_luminance': local_std(luminance, 5),
              'unclipped_linear_luminance': luminance,
              'any_rgb_high_clipped': np.any(rgb >= 1., axis=-1),
              'all_rgb_high_clipped': np.all(rgb >= 1., axis=-1),
              'any_rgb_low_clipped': np.any(rgb <= 0., axis=-1),
              'angle_window_same_instance': s.mask_interior(ids, radius)}
    settings = {'angle_matched_kernel': k, 'kernel_reference': 'small +/-2 pixel-centre span',
                'focal_px': focal, 'small_same_gaze_focal_px': fsmall,
                'production_5_centre_span_rad_approx': 4 / focal,
                'diagnostic_centre_span_rad_approx': 2 * radius / focal,
                'warning': 'Scores only. Matcher, refinement and accepted mask are NOT changed. '
                           'A gradient may contain noise and is not calibrated confidence.'}
    return fields, settings


def trace_rgb(c: dict, obs: dict, stored: dict) -> dict:
    """RGB/calibration/IDs only. No folder, ground truth, or evaluator input."""
    fresh, meta = s.compute(c, obs)
    assert_replay(stored, fresh)
    r = s.rectification(c)
    w, h = c['image_size_wh']
    x, y, cw, ch = map(int, r['crop_xywh'])
    sl = np.s_[y:y + ch, x:x + cw]
    colours = {}; gray = {}; ids = {}; support = {}
    for side in ('L', 'R'):
        colours[side] = s.remap(obs['rgb_' + side], r, side, cv2.INTER_LINEAR)
        gray[side] = cv2.cvtColor(s.linear_to_u8(colours[side]), cv2.COLOR_RGB2GRAY)
        ids[side] = s.remap(obs['instance_' + side].astype(np.float32), r, side,
                            cv2.INTER_NEAREST).astype(np.int32)
        support[side] = s.support_mask(c, r, side) & s.mask_interior(ids[side], s.INSTANCE_GUARD_PX)
    minimum = int(r['min_disparity']); nd = int(r['num_disparities'])
    min_right = -(minimum + nd - 1)
    # Right initial-validity was not saved, so reproduce this one frozen operation.
    dr_raw = s.matcher(min_right, nd).compute(gray['R'], gray['L'])
    vr = dr_raw > (min_right - 1) * 16
    uv = g.pixels(cw, ch) + [x, y]
    dl = fresh['disparity_px']
    ur = uv[..., 0] - dl
    xx = ur.astype(np.float32); yy = uv[..., 1].astype(np.float32)
    rem = lambda a, mode: cv2.remap(a, xx, yy, mode, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    dr_at = rem(fresh['disparity_right_full_px'], cv2.INTER_LINEAR)
    vr_at = rem((vr & support['R']).astype(np.float32), cv2.INTER_LINEAR) > .999
    rid = rem(ids['R'].astype(np.float32), cv2.INTER_NEAREST).astype(np.int32)
    lr = np.abs(dl + dr_at)
    require(np.array_equal(lr, fresh['lr_error_px']), 'LR tracing differs from production')
    zrect = g.reproject_q(r['Q_full'], uv, dl)
    xyz = g.rect_to_head(c, r['R1'], zrect)
    lo, hi = c['depth_search_z_rect_m']
    roi = cv2.getValidDisparityROI(tuple(r['roi_L']), tuple(r['roi_R']), minimum, nd, s.BLOCK_SIZE)
    gx, gy, gw, gh = roi
    region = np.zeros((h, w), bool); region[gy:gy + gh, gx:gx + gw] = True
    m = gray['L'].astype(np.float32)
    std = np.sqrt(np.maximum(cv2.boxFilter(m * m, -1, (5, 5)) - cv2.boxFilter(m, -1, (5, 5)) ** 2, 0.))[sl]
    require(np.array_equal(std, fresh['left_gray_std']), 'texture tracing differs from production')
    masks = {'left_disparity_valid': fresh['disparity_sgbm_px'] > minimum - 1,
             'right_match_supported': vr_at, 'left_supported': support['L'][sl],
             'right_in_raster': (ur >= 0) & (ur < w - 1),
             'lr_consistent': lr <= s.LR_TOLERANCE_PX,
             'same_instance': rid == ids['L'][sl],
             'texture': std >= s.MIN_LOCAL_STD_U8,
             'finite_range_in_bounds': np.isfinite(zrect).all(axis=-1) & (zrect[..., 2] >= lo) & (zrect[..., 2] <= hi),
             'disparity_roi': region[sl]}
    require(np.array_equal(intersect(masks), stored['valid']), 'gate conjunction differs from saved validity')
    groups = partition(masks); check_partition(groups, np.ones((ch, cw), bool))
    fields, settings = diagnostic_fields(c, r, colours['L'], ids['L'])
    fields = {key: value[sl] for key, value in fields.items()}
    fields['std5_production'] = std
    fields['lr_error_px'] = lr
    rect_raw = g.reproject_q(r['Q_full'], uv, fresh['disparity_sgbm_px'])
    return {'fresh': fresh, 'meta': meta, 'masks': masks, 'groups': groups,
            'xyz_refined': xyz, 'xyz_sgbm': g.rect_to_head(c, r['R1'], rect_raw),
            'fields': fields, 'settings': settings}


def describe_cohort(mask: np.ndarray, reference: np.ndarray, trace: dict, truth: dict, centre: np.ndarray,
                    include_geometry: bool = True) -> dict:
    a = mask & reference
    count = int(a.sum()); total = int(reference.sum())
    result = {'pixels': count, 'fraction_of_reference': count / total if total else None,
              'diagnostic_fields': {k: distribution(v[a]) for k, v in trace['fields'].items() if v.dtype != bool},
              'boolean_field_fractions': {k: float(np.mean(v[a])) if count else None
                                          for k, v in trace['fields'].items() if v.dtype == bool}}
    if include_geometry:
        result['refined_on_this_exact_cohort'] = e.describe_errors(trace['xyz_refined'], truth, centre, a, a)
        result['sgbm_on_this_exact_cohort'] = e.describe_errors(trace['xyz_sgbm'], truth, centre, a, a)
    return result


def reference_report(ref: np.ndarray, trace: dict, truth: dict, centre: np.ndarray) -> dict:
    groups = trace['groups']; check_partition(groups, ref)
    rejected = ref & ~groups['accepted']
    texture_fails = ~trace['masks']['texture']
    only = groups['texture_only_veto']
    f = trace['fields']
    angle_evidence = only & f['angle_window_same_instance'] & (f['std_angle_matched_u8'] >= s.MIN_LOCAL_STD_U8)
    cohorts = {name: describe_cohort(mask, ref, trace, truth, centre, name != 'other_veto')
               for name, mask in groups.items()}
    cohorts['texture_only_u8_score_zero'] = describe_cohort(only & (f['std5_production'] == 0), ref, trace, truth, centre)
    cohorts['texture_only_all_rgb_high_clipped'] = describe_cohort(only & f['all_rgb_high_clipped'], ref, trace, truth, centre)
    cohorts['texture_only_angle_window_has_contrast'] = describe_cohort(angle_evidence, ref, trace, truth, centre)
    pre = groups['accepted'] | only
    return {'reference_pixels': int(ref.sum()),
            'reference_status': 'EXERCISED' if np.any(ref) else 'NOT_EXERCISED',
            'rejected_pixels': int(rejected.sum()),
            'rejected_with_texture_failure': int((rejected & texture_fails).sum()),
            'failure_counts_overlap': {name: int((ref & ~mask).sum()) for name, mask in trace['masks'].items()},
            'cohorts': cohorts,
            'counterfactual_without_texture_veto_DIAGNOSTIC_ONLY':
                e.describe_errors(trace['xyz_refined'], truth, centre, pre, ref),
            'official_mask_metrics': e.describe_errors(trace['fresh']['xyz_h'], truth, centre, groups['accepted'], ref)}


def verify_official_metrics(report: dict, official: dict) -> None:
    for key in ('reference_pixels', 'accepted_pixels', 'coverage', 'median_relative_range_error', 'p95_relative_range_error'):
        a, b = report[key], official[key]
        require((a is None and b is None) or (a is not None and b is not None and
                np.isclose(a, b, rtol=1e-10, atol=1e-12)), f'official metric mismatch: {key}')


def make_visual(out: Path, trace: dict, truth: dict, ref: np.ndarray, boundary: np.ndarray, centre: np.ndarray) -> None:
    size = 256
    def byte(a): return np.rint(255 * np.clip(np.nan_to_num(a, nan=0), 0, 1)).astype(np.uint8)
    groups = trace['groups']; fields = trace['fields']
    pred_range = np.linalg.norm(trace['xyz_refined'] - centre, axis=-1)
    with np.errstate(divide='ignore', invalid='ignore'):
        err = np.abs(pred_range - truth['range_m']) / truth['range_m']
    candidate = ref & groups['texture_only_veto']
    panels = [('RGB display (clipped by baseline)', s.linear_to_u8(trace['fresh']['rgb_left'])),
              ('Official accepted interior', byte(ref & groups['accepted'])),
              ('Texture-only veto / interior', byte(candidate)),
              ('Other veto / interior', byte(ref & groups['other_veto'])),
              ('Production std5 / 0.5', byte(fields['std5_production'] / .5)),
              ('Float-display std5 / 0.5', byte(fields['std5_float_display'] / .5)),
              (f"Angle std{trace['settings']['angle_matched_kernel']} / 0.5", byte(fields['std_angle_matched_u8'] / .5)),
              ('Rejected hypothesis error / 3%', byte(np.where(candidate, err / .03, 0))),
              ('Fixed evaluator boundary', byte(boundary)),
              ('All RGB channels >= 1 (clipped)', byte(fields['all_rgb_high_clipped'])),
              ('Linear std5 / own p95', byte(fields['std5_unclipped_linear_luminance'] / max(float(np.quantile(fields['std5_unclipped_linear_luminance'], .95)), 1e-12))),
              ('Horizontal gradient RMS / p95', byte(fields['gradient_x_rms_linear'] / max(float(np.quantile(fields['gradient_x_rms_linear'], .95)), 1e-12)))]
    canvas = Image.new('RGB', (3 * size, 4 * (size + 28) + 48), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 6), 'DIAGNOSTIC ONLY - rejected hypotheses are not accepted geometry', fill='black')
    draw.text((8, 24), 'Black outside each support. No depth filling; no estimator changes.', fill='black')
    for i, (label, data) in enumerate(panels):
        x = (i % 3) * size; y = 48 + (i // 3) * (size + 28)
        draw.text((x + 5, y + 5), label, fill='black')
        image = Image.fromarray(data).convert('RGB').resize((size, size), Image.Resampling.NEAREST)
        canvas.paste(image, (x, y + 28))
    canvas.save(out / 'diagnostic.png')


def snapshot(runs: list[Path]) -> dict:
    # Preserve all numerical records, input hashes, and historical evaluation JSON.
    return {str(p): s.sha256(p) for run in runs for p in sorted(run.rglob('*'))
            if p.is_file() and p.suffix in {'.npz', '.json'}}


def validate_paths(runs: list[Path], out: Path) -> tuple[list[Path], Path]:
    runs = [p.resolve() for p in runs]; out = out.resolve()
    require(len(set(runs)) == len(runs), 'duplicate input run')
    require(len(set(p.name for p in runs)) == len(runs), 'run names must be unique')
    require(not out.exists(), f'output already exists: {out}')
    for run in runs:
        require(run.is_dir(), f'input run missing: {run}')
        require(not out.is_relative_to(run) and not run.is_relative_to(out), 'output and input paths overlap')
    return runs, out


def audit_run(run: Path, out: Path, allow_synthetic: bool = False) -> dict:
    runmeta = json.loads((run / 'run.json').read_text())
    require(bool(runmeta.get('complete')), 'incomplete run')
    require(set(runmeta['cases']) == {'fronto', 'tilted', 'step'}, 'requires the unchanged three-case suite')
    suite = {'run': str(run), 'source': runmeta['source'], 'profile': runmeta['profile'],
             'spp': runmeta['spp'], 'cases': {}, 'new_primary_samples': 0}
    for name in runmeta['cases']:
        folder = run / name
        acq = json.loads((folder / 'acquisition.json').read_text())
        real = acq.get('source') == 'blender_cycles' and acq.get('checks', {}).get('independent_blender_checks')
        require(bool(real) or allow_synthetic, 'not a checked Blender measurement')
        summary = json.loads((folder / 'stereo' / 'summary.json').read_text())
        for path, value in summary['input_sha256'].items():
            require(s.sha256(folder / path) == value, f'stale input: {name}/{path}')
        c = json.loads((folder / 'calibration.json').read_text())
        obs = load_npz(folder / 'observation.npz')
        stored = load_npz(folder / 'stereo' / 'result.npz')
        trace = trace_rgb(c, obs, stored)
        # Everything before this point is computed without truth. Everything after
        # this point is evaluator-side analysis and cannot alter the saved model.
        truth, eligible, band, monocular = e.ground_reference(c, load_npz(folder / 'evaluation_only' / 'mesh.npz'))
        refs = {'interior': eligible & ~band, 'boundary': eligible & band, 'singly_visible': monocular}
        for ident in sorted(set(truth['instance_id'][eligible].tolist()) - {0}):
            refs[f'instance_{ident}_interior'] = eligible & ~band & (truth['instance_id'] == ident)
        centre = np.asarray(c['eyes'][0]['centre_h_m'])
        reports = {key: reference_report(ref, trace, truth, centre) for key, ref in refs.items()}
        # Use the original evaluator in non-writing mode. A FAIL is expected and
        # preserved; its original population and metrics must reproduce exactly.
        original = e.evaluate_pair(folder, allow_synthetic=allow_synthetic, write=False)
        for key in ('interior', 'boundary', 'singly_visible'):
            verify_official_metrics(reports[key]['official_mask_metrics'], original[key])
        for ident, metrics in original['per_object_interior'].items():
            key = f'instance_{ident}_interior'
            if key in reports: verify_official_metrics(reports[key]['official_mask_metrics'], metrics)
        result = {'case': name, 'diagnostic_only': True, 'replay_exact': True,
                  'baseline_checks_pass': original['checks_pass'], 'baseline_failures': original['fails'],
                  'settings': trace['settings'], 'reference_groups': reports,
                  'synthetic_not_renderer': not bool(real)}
        dest = out / run.name / name; dest.mkdir(parents=True)
        g.json_write(dest / 'audit.json', result)
        make_visual(dest, trace, truth, eligible & ~band, eligible & band, centre)
        suite['cases'][name] = result
        for key, report in reports.items():
            if key not in ('interior',) and not key.startswith('instance_'): continue
            old = report['official_mask_metrics']; extra = report['cohorts']['texture_only_veto']
            quality = extra['refined_on_this_exact_cohort']
            print(f"[fsg-audit] {run.name}/{name}/{key} reference={report['reference_pixels']} "
                  f"official_coverage={old['coverage']} texture_only={extra['pixels']} "
                  f"rejected_median={quality['median_relative_range_error']} rejected_p95={quality['p95_relative_range_error']}")
    return suite


def audit(runs: list[Path], out: Path, allow_synthetic: bool = False) -> dict:
    t0 = time.perf_counter(); sources = check_sources()
    runs, out = validate_paths(runs, out)
    before = snapshot(runs)
    results = [audit_run(run, out, allow_synthetic) for run in runs]
    after = snapshot(runs)
    require(before == after, 'input records changed during audit')
    require(check_sources() == sources, 'frozen sources changed during audit')
    report = {'schema': 'FSG1-coverage-audit-v1', 'status': 'AUDIT_COMPLETE_NOT_A_MILESTONE',
              'diagnostic_only': True, 'fsg1_authorized_pass': False,
              'new_primary_samples': 0, 'frozen_source_sha256': sources,
              'input_sha256_before': before, 'input_sha256_after': after,
              'inputs_unchanged': True, 'numpy': np.__version__, 'opencv': cv2.__version__,
              'runs': results, 'seconds': time.perf_counter() - t0,
              'limits': 'Post-hoc diagnostic on saved seed(s); no new configuration, acceptance rule, '
                        'surface completion or causal noise/resolution conclusion.'}
    g.json_write(out / 'audit.json', report)
    print(f"[fsg-audit] AUDIT_COMPLETE_NOT_A_MILESTONE runs={len(results)} inputs_unchanged=true "
          f"new_primary_samples=0 seconds={report['seconds']:.3f}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path, nargs='+')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-synthetic', action='store_true', help='software tests only; never a renderer result')
    args = parser.parse_args()
    audit(args.runs, args.out, args.allow_synthetic)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'[fsg-audit] FAIL {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
