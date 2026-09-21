"""Aggregate the twelve prospectively fixed Scene-1c component controls."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import scene1c_public as public
from fsg_geometry import json_write

EXPECTED=set(public.expected_component_trials())


def compare(metric_files:list[Path],out:Path)->dict:
    out=out.resolve()
    if out.exists(): raise FileExistsError("certification output must be new")
    rows=[]; seen=set(); fails=[]
    for p in metric_files:
        r=json.loads(p.resolve().read_text()); key=(r["fixture"],int(r["seed"]),int(r["object_id"]))
        if key in seen: raise ValueError("duplicate Scene-1c component control")
        seen.add(key); rows.append(r)
    if seen!=EXPECTED:
        missing=sorted(EXPECTED-seen); extra=sorted(seen-EXPECTED)
        fails.append(f"component control set incomplete missing={missing} extra={extra}")
    rows.sort(key=lambda r:(r["fixture"],int(r["seed"]),int(r["object_id"])))
    for r in rows:
        if r.get("profile")!="full": fails.append(f"{r['fixture']}/{r['seed']}/{r['object_id']} is not full profile")
        if r.get("status")!="SCENE1C_COMPONENT_RUN_PASS" or r.get("fails"): fails.append(f"{r['fixture']}/{r['seed']}/{r['object_id']} component control failed")
    result={"schema":"Scene1c-component-certification-v1","public_spec_sha256":public.public_digest(),"controls":rows,"control_passes":sum(not r.get("fails") for r in rows),"control_count":len(rows),"expected_control_count":len(EXPECTED),"fails":fails,
            "status":public.COMPONENT_CERTIFICATION_STATUS_PASS if not fails else public.COMPONENT_CERTIFICATION_STATUS_FAIL}
    out.mkdir(parents=True); json_write(out/"certification.json",result); print("[scene1c-certify-compare] "+result["status"],json.dumps(result,sort_keys=True),flush=True); return result


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("metrics",nargs="+",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); r=compare(a.metrics,a.out); raise SystemExit(0 if not r["fails"] else 2)
if __name__=="__main__": main()
