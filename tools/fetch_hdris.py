"""Find and download Poly Haven HDRIs (CC0) for tier-1 scenes. Standard library only.

    python tools/fetch_hdris.py list --environment indoor --min-width 16384 --top 20
    python tools/fetch_hdris.py search "workshop tools" --top 10
    python tools/fetch_hdris.py get <slug> [<slug> ...] --res 8k --fmt exr --out scenes/hdri

Resolution guide: equirect width / 360 = px per degree. 8k (8192) = 22.8 px/deg, enough for a
reference at s0 = 0.05 deg; 16k = 45.5 px/deg.
API: https://api.polyhaven.com (assets CC0; "Powered by Poly Haven" credit if you build on the live API).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.polyhaven.com"
HEADERS = {"User-Agent": "visgraf-foveation-scene-gathering/0.1"}


def get_json(path: str, **params) -> object:
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as resp:
        return json.load(resp)


def as_items(assets: object) -> list[tuple[str, dict]]:
    if isinstance(assets, dict):
        return list(assets.items())
    return [(a.get("id") or a.get("slug"), a) for a in assets]  # tolerate list form


def row(slug: str, info: dict) -> str:
    w, h = (info.get("max_resolution") or [0, 0])[:2]
    env = (info.get("attributes") or {}).get("environment", "?")
    return f"{slug:40s} {w:>6}x{h:<6} {env:8s} {info.get('category') or ','.join(info.get('categories', []))}"


def cmd_list(args):
    params = {"type": "hdris"}
    if args.environment:
        params["environment"] = args.environment
    items = [(s, i) for s, i in as_items(get_json("/assets", **params))
             if (i.get("max_resolution") or [0])[0] >= args.min_width]
    items.sort(key=lambda si: (-(si[1].get("max_resolution") or [0])[0], -si[1].get("download_count", 0)))
    for slug, info in items[: args.top]:
        print(row(slug, info))
    print(f"({len(items)} matching)")


def cmd_search(args):
    res = get_json("/search", q=args.query.strip().lower(), t="hdris", limit=args.top)
    for r in res.get("results", []):
        print(row(r["slug"], get_json(f"/info/{r['slug']}")))


def download(url: str, dest: str, md5: str | None) -> None:
    tmp = dest + ".part"
    h = hashlib.md5()
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as resp, open(tmp, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:8.1f} / {total / 1e6:.1f} MB", end="", flush=True)
    print()
    if md5 and h.hexdigest() != md5:
        os.remove(tmp)
        raise RuntimeError(f"md5 mismatch for {url}")
    os.replace(tmp, dest)


def cmd_get(args):
    for slug in args.slugs:
        files = get_json(f"/files/{slug}")
        hdri = files.get("hdri", {})
        if args.res not in hdri or args.fmt not in hdri[args.res]:
            avail = {r: sorted(f) for r, f in hdri.items()}
            print(f"{slug}: {args.res}/{args.fmt} not available; have {avail}", file=sys.stderr)
            continue
        entry = hdri[args.res][args.fmt]
        folder = os.path.join(args.out, slug)
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, os.path.basename(urllib.parse.urlparse(entry["url"]).path))
        if os.path.exists(dest):
            print(f"{slug}: already have {dest}")
        else:
            print(f"{slug}: downloading {entry['url']}")
            download(entry["url"], dest, entry.get("md5"))
        info = get_json(f"/info/{slug}")
        meta = {"slug": slug, "name": info.get("name"), "authors": info.get("authors"),
                "license": "CC0", "source_api": f"{API}/info/{slug}", "file": os.path.basename(dest),
                "url": entry["url"], "md5": entry.get("md5"), "resolution": args.res,
                "max_resolution": info.get("max_resolution"), "category": info.get("category"),
                "attributes": info.get("attributes"), "tags": info.get("tags")}
        with open(os.path.join(folder, "asset.json"), "w") as fh:
            json.dump(meta, fh, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--environment", choices=["indoor", "outdoor"])
    p.add_argument("--min-width", type=int, default=8192)
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--top", type=int, default=10)
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser("get")
    p.add_argument("slugs", nargs="+")
    p.add_argument("--res", default="8k")
    p.add_argument("--fmt", default="exr", choices=["exr", "hdr"])
    p.add_argument("--out", default="scenes/hdri")
    p.set_defaults(fn=cmd_get)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
