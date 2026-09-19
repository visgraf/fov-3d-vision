"""FSG1c: evaluate ONE fixed encoding candidate on existing observations.

  python tools/fsg_hdr_compare.py RUN [RUN ...] --out NEW_DIRECTORY
No rendering, retuning, legacy overwrite, or milestone promotion. Predictions
are written before any ground-truth access in this comparison. The inference
module fsg_stereo_hdr never imports an evaluator or opens evaluation_only/.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import cv2
from PIL import Image, ImageDraw
import fsg_geometry as g
import fsg_stereo as s
import fsg_stereo_hdr as h
import fsg_evaluate as e
import fsg_coverage_audit as a


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def snapshot(runs: list[Path]) -> dict:
    """Hash ALL files, including visuals and optional .blend, in bounded memory."""
    result = {}
    for root in runs:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                with path.open('rb') as f:
                    result[str(path)] = hashlib.file_digest(f, 'sha256').hexdigest()
    return result


def candidate_evaluation(c: dict, result: dict, mesh: dict,
                         real: bool, allow_synthetic: bool) -> tuple[dict, dict]:
    truth, eligible, band, mono = e.ground_reference(c, mesh)
    centre = np.asarray(c['eyes'][0]['centre_h_m'])
    require(result['xyz_h'].shape == truth['position_h'].shape, 'candidate/reference shape mismatch')
    refs = {'interior': eligible & ~band, 'boundary': eligible & band,
            'singly_visible': mono, 'jointly_visible_all': eligible}
    refs.update({f'instance_{i}_interior': eligible & ~band & (truth['instance_id'] == i)
                 for i in sorted(set(mesh['instance_ids'].tolist()))})
    metrics = {key: e.describe_errors(result['xyz_h'], truth, centre, result['valid'], ref)
               for key, ref in refs.items()}
    fails = e.gate(metrics['interior'])
    for key in refs:
        if key.startswith('instance_') and metrics[key]['reference_pixels'] >= 100:
            fails += [f'{key}: {x}' for x in e.gate(metrics[key])]
    wrong = (result['instance_id'] != truth['instance_id']) & result['valid'] & eligible
    if np.any(wrong & ~band):
        fails.append('accepted interior has incorrect object identity')
    if not real and not allow_synthetic:
        fails.append('not a checked Blender measurement')
    return {'metrics': metrics, 'fails': fails, 'checks_pass': not fails,
            'wrong_instance_accepted_count': int(wrong.sum()),
            'reference_status': {k: 'EXERCISED' if np.any(v) else 'NOT_EXERCISED' for k, v in refs.items()},
            'thresholds': {'minimum_coverage': e.MIN_COVERAGE,
                'maximum_median_relative_range': e.MAX_MEDIAN_RELATIVE_RANGE,
                'maximum_p95_relative_range': e.MAX_P95_RELATIVE_RANGE,
                'boundary_radius_px': e.BOUNDARY_RADIUS[c['profile']]}}, \
           {'truth': truth, 'refs': refs, 'centre': centre}


def paired_metrics(trace: dict, candidate: dict, context: dict) -> dict:
    truth, centre = context['truth'], context['centre']
    old = trace['fresh']; left = old['valid']; right = candidate['valid']
    common = left & right
    old_texture = trace['groups']['texture_only_veto']
    # Four mutually exclusive regions describe genuine re-estimation, not filling.
    partition = {'common': common, 'newly_accepted': right & ~left,
                 'lost': left & ~right, 'neither': ~left & ~right}
    require(np.all(sum(v.astype(np.uint8) for v in partition.values()) == 1), 'paired partition invalid')
    output = {}
    for key, ref in context['refs'].items():
        report = {'reference_pixels': int(ref.sum()),
                  'mask_counts': {n: int((ref & v).sum()) for n, v in partition.items()},
                  'old_texture_only_count': int((ref & old_texture).sum()),
                  'old_texture_only_now_accepted': int((ref & old_texture & right).sum()),
                  'legacy': e.describe_errors(old['xyz_h'], truth, centre, left, ref),
                  'candidate': e.describe_errors(candidate['xyz_h'], truth, centre, right, ref),
                  'common_legacy': e.describe_errors(old['xyz_h'], truth, centre, common, ref & common),
                  'common_candidate': e.describe_errors(candidate['xyz_h'], truth, centre, common, ref & common),
                  'newly_accepted_candidate': e.describe_errors(candidate['xyz_h'], truth, centre,
                                                               partition['newly_accepted'], ref & partition['newly_accepted']),
                  'old_texture_only_legacy_hypotheses_DIAGNOSTIC': e.describe_errors(
                      trace['xyz_refined'], truth, centre, old_texture, ref & old_texture),
                  'old_texture_only_candidate': e.describe_errors(candidate['xyz_h'], truth, centre,
                                                                  right, ref & old_texture)}
        masks = {'all_reference': ref, 'old_texture_only': ref & old_texture}
        report['score_distributions'] = {n: {
            'legacy_std5_u8': a.distribution(old['left_gray_std'][m]),
            'candidate_std5_u8': a.distribution(candidate['left_gray_std'][m]),
            'candidate_below_texture_cutoff_fraction': float(np.mean(candidate['left_gray_std'][m] < s.MIN_LOCAL_STD_U8)) if np.any(m) else None,
            'candidate_all_channels_255_fraction': float(np.mean(np.all(h.hdr_to_u8(candidate['rgb_left'])[m] == 255, axis=-1))) if np.any(m) else None}
            for n, m in masks.items()}
        output[key] = report
    return output


def make_visual(out: Path, trace: dict, candidate: dict, context: dict) -> None:
    old = trace['fresh']; ref = context['refs']['interior']; truth = context['truth']
    def byte(x):
        return np.rint(255 * np.clip(np.nan_to_num(x, nan=0.), 0., 1.)).astype(np.uint8)
    with np.errstate(invalid='ignore', divide='ignore'):
        err = np.abs(np.linalg.norm(candidate['xyz_h'] - context['centre'], axis=-1) - truth['range_m']) / truth['range_m']
    panels = [('Legacy clipped RGB', s.linear_to_u8(old['rgb_left'])),
              ('Candidate fixed soft HDR RGB', h.hdr_to_u8(candidate['rgb_left'])),
              ('Candidate error / 3% (valid only)', byte(np.where(candidate['valid'] & ref, err / .03, 0))),
              ('Legacy valid interior', byte(old['valid'] & ref)),
              ('Candidate valid interior', byte(candidate['valid'] & ref)),
              ('Newly accepted / interior', byte(candidate['valid'] & ~old['valid'] & ref)),
              ('Legacy std5 / 0.5', byte(old['left_gray_std'] / .5)),
              ('Candidate std5 / 0.5', byte(candidate['left_gray_std'] / .5)),
              ('Lost support / interior', byte(old['valid'] & ~candidate['valid'] & ref))]
    size = 256; height = 30; top = 52
    canvas = Image.new('RGB', (3 * size, 3 * (size + height) + top), 'white'); draw = ImageDraw.Draw(canvas)
    draw.text((8, 7), 'FSG1c FIXED CANDIDATE - existing observations, no promotion', fill='black')
    draw.text((8, 27), 'Missing is black. Read validity separately from the error panel.', fill='black')
    for i, (label, data) in enumerate(panels):
        x, y = i % 3 * size, top + i // 3 * (size + height)
        draw.text((x + 4, y + 5), label, fill='black')
        canvas.paste(Image.fromarray(data).convert('RGB').resize((size, size), Image.Resampling.NEAREST), (x, y + height))
    canvas.save(out / 'comparison.png')


def compare_run(run: Path, out: Path, allow_synthetic: bool) -> dict:
    meta = json.loads((run / 'run.json').read_text())
    require(meta.get('complete') is True, 'incomplete run')
    require(len(meta['cases']) == 3 and set(meta['cases']) == {'fronto', 'tilted', 'step'}, 'requires unchanged three-case suite')
    cases = {}; all_real = True
    for name in meta['cases']:
        folder = run / name
        c, obs = h.read_observation(folder)
        acq = json.loads((folder / 'acquisition.json').read_text())
        real = acq.get('source') == 'blender_cycles' and bool(acq.get('checks', {}).get('independent_blender_checks'))
        require(real or allow_synthetic, 'not a checked Blender record; synthetic inputs forbidden here')
        all_real &= real
        summary = json.loads((folder / 'stereo' / 'summary.json').read_text())
        require(set(summary['input_sha256']) == {'calibration.json', 'observation.npz'}, 'unexpected legacy input fingerprints')
        for file, digest in summary['input_sha256'].items():
            require(s.sha256(folder / file) == digest, f'stale legacy input: {name}/{file}')
        stored = a.load_npz(folder / 'stereo' / 'result.npz')
        # Replay and new RGB inference both precede ground-truth access.
        trace = a.trace_rgb(c, obs, stored)
        result, candidate_meta = h.compute_candidate(c, obs)
        candidate_meta['input_sha256'] = dict(summary['input_sha256'])
        candidate_meta['legacy_record_path'] = str(folder)
        dest = out / run.name / name
        h.save_candidate(dest / 'stereo_candidate', c, result, candidate_meta)
        # Evaluator-side code below cannot change a prediction already saved.
        old_metrics = e.evaluate_pair(folder, allow_synthetic=allow_synthetic, write=False)
        mesh = a.load_npz(folder / 'evaluation_only' / 'mesh.npz')
        new_metrics, context = candidate_evaluation(c, result, mesh, real, allow_synthetic)
        paired = paired_metrics(trace, result, context)
        for key in ('interior', 'boundary', 'singly_visible'):
            a.verify_official_metrics(paired[key]['legacy'], old_metrics[key])
        for ident, value in old_metrics['per_object_interior'].items():
            a.verify_official_metrics(paired[f'instance_{ident}_interior']['legacy'], value)
        report = {'case': name, 'candidate_id': h.CANDIDATE_ID, 'legacy_replay_exact': True,
                  'legacy': old_metrics, 'candidate': new_metrics, 'paired': paired,
                  'real_blender_input': real, 'candidate_stereo_seconds': candidate_meta['seconds'],
                  'new_primary_samples': 0, 'baseline_preserved': True,
                  'full_profile_milestone_pass': False, 'fusion_authorized': False}
        g.json_write(dest / 'comparison.json', report)
        make_visual(dest, trace, result, context)
        cases[name] = report
        for key, values in new_metrics['metrics'].items():
            if key != 'interior' and not key.startswith('instance_'):
                continue
            print(f"[fsg-hdr] {run.name}/{name}/{key} reference={values['reference_pixels']} "
                  f"coverage={values['coverage']} median={values['median_relative_range_error']} "
                  f"p95={values['p95_relative_range_error']}")
        for message in new_metrics['fails']:
            print(f'[fsg-hdr] CANDIDATE_FAIL {run.name}/{name}: {message}')
    fails = [f'{name}: {x}' for name, values in cases.items() for x in values['candidate']['fails']]
    status = 'CANDIDATE_FAIL_ON_EXISTING_RECORD' if fails else (
        'SYNTHETIC_CANDIDATE_PASS_NOT_A_RENDER_RESULT' if not all_real else 'CANDIDATE_PASS_ON_EXISTING_RECORD')
    return {'run': str(run), 'profile': meta['profile'], 'spp': meta['spp'], 'source': meta['source'],
            'real_blender_input': all_real, 'status': status, 'candidate_checks_pass': not fails,
            'full_profile_milestone_pass': False, 'adopted_default': False, 'cases': cases, 'fails': fails,
            'original_primary_camera_samples': sum(x['legacy']['primary_camera_samples'] for x in cases.values()),
            'new_primary_samples': 0}


def compare(runs: list[Path], out: Path, allow_synthetic: bool = False) -> dict:
    require(bool(runs), 'at least one input run is required')
    start = time.perf_counter(); frozen = a.check_sources(); h.check_kernel_equivalence()
    runs, out = a.validate_paths(runs, out)
    before = snapshot(runs)
    results = []
    try:
        # A numerical candidate miss is a RESULT, not an excuse to skip the other
        # prescribed profiles. Exceptions and failed replay guards STOP immediately.
        for run in runs:
            results.append(compare_run(run, out, allow_synthetic))
    finally:
        after = snapshot(runs)
        require(before == after, 'INPUT FILES CHANGED; discard candidate interpretation')
        require(a.check_sources() == frozen, 'frozen source files changed')
        h.check_kernel_equivalence()
    report = {'schema': 'FSG1c-HDR-comparison-v1', 'status': 'CANDIDATE_COMPARISON_COMPLETE_NOT_A_MILESTONE',
              'candidate_id': h.CANDIDATE_ID, 'encoding': h.ENCODING, 'inputs_unchanged': True,
              'all_requested_candidate_gates_pass': all(r['candidate_checks_pass'] for r in results),
              'full_profile_milestone_pass': False, 'fusion_authorized': False, 'adopted_default': False,
              'new_primary_samples': 0, 'frozen_source_sha256': frozen,
              'input_sha256_before': before, 'input_sha256_after': after,
              'candidate_source_sha256': {n: s.sha256(Path(__file__).parent / n)
                                         for n in ('fsg_stereo_hdr.py', 'fsg_hdr_compare.py')},
              'numpy': np.__version__, 'opencv': cv2.__version__, 'runs': results,
              'seconds': time.perf_counter() - start,
              'limitation': 'Development-set comparison. Same seed-17 records informed the candidate. '
                            'No independent validation, held-out nonplanar evidence, or half-occlusion claim.'}
    g.json_write(out / 'comparison.json', report)
    print(f"[fsg-hdr] SUMMARY runs={len(results)} inputs_unchanged=true new_primary_samples=0 "
          f"all_requested_candidate_gates_pass={str(report['all_requested_candidate_gates_pass']).lower()} "
          f"seconds={report['seconds']:.3f} status={report['status']}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path, nargs='+'); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-synthetic', action='store_true', help='software checks only, never renderer validation')
    args = parser.parse_args()
    report = compare(args.runs, args.out, args.allow_synthetic)
    # Exit 2 distinguishes a finished comparison with an expected scientific miss
    # from exit 1 for a software/provenance/integrity exception.
    raise SystemExit(0 if report['all_requested_candidate_gates_pass'] else 2)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'[fsg-hdr] FAIL {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
