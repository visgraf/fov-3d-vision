"""Aggregate certified components plus the four Scene-1c ensemble trials."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import scene1c_public as public
from fsg_geometry import json_write
EXPECTED={(f,s) for f in public.FIXTURES for s in public.SEEDS}


def compare(metric_files:list[Path],certification_file:Path,out:Path)->dict:
    out=out.resolve()
    if out.exists(): raise FileExistsError("comparison output must be new")
    cert=json.loads(certification_file.resolve().read_text()); fails=[]
    if cert.get("public_spec_sha256")!=public.public_digest(): fails.append("component certification public-spec digest mismatch")
    if cert.get("status")!=public.COMPONENT_CERTIFICATION_STATUS_PASS or cert.get("fails"): fails.append("component certification prerequisite did not pass")
    if int(cert.get("control_passes",-1))!=len(public.expected_component_trials()): fails.append("not all prospective component controls passed")
    rows=[]; seen=set()
    for p in metric_files:
        r=json.loads(p.resolve().read_text()); key=(r["fixture"],int(r["seed"]))
        if key in seen: raise ValueError("duplicate Scene-1c trial")
        seen.add(key); rows.append(r)
    if seen!=EXPECTED: raise ValueError(f"Scene-1c full set incomplete: got {sorted(seen)} expected {sorted(EXPECTED)}")
    rows.sort(key=lambda r:(r["fixture"],r["seed"]))
    for r in rows:
        if r["profile"]!="full": fails.append(f"{r['fixture']}/{r['seed']} is not full profile")
        if r["status"]!="SCENE1C_RUN_PASS" or r["fails"]: fails.append(f"{r['fixture']}/{r['seed']} scene run failed")
    result={"schema":"Scene1c-comparison-v1","component_certification_status":cert.get("status"),"component_control_passes":int(cert.get("control_passes",0)),
            "trials":rows,"trial_passes":sum(not r["fails"] for r in rows),"mean_scene_final_coverage":float(np.mean([r["scene_mean_final_coverage"] for r in rows])),
            "min_object_final_coverage":float(min(r["scene_min_final_coverage"] for r in rows)),"mean_fixation_count":float(np.mean([r["fixation_count"] for r in rows])),
            "fails":fails,"status":public.STAGE_STATUS_PASS if not fails else public.STAGE_STATUS_FAIL}
    out.mkdir(parents=True); json_write(out/"comparison.json",result); print("[scene1c-compare] "+result["status"],json.dumps(result,sort_keys=True),flush=True); return result


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("metrics",nargs=4,type=Path); ap.add_argument("--certification",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); r=compare(a.metrics,a.certification,a.out); raise SystemExit(0 if not r["fails"] else 2)
if __name__=="__main__": main()
