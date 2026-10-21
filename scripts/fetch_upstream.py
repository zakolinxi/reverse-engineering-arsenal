#!/usr/bin/env python3
"""Browse, check and shallow-clone the upstream projects catalogued by this skill.

The catalog is the machine-readable contract that no capability from the original
source list is lost: every source is recorded with its category, capabilities and
reference section.

Examples:
  python fetch_upstream.py list
  python fetch_upstream.py list --category js
  python fetch_upstream.py check --limit 5
  python fetch_upstream.py fetch js-reverse-mcp frida --dest ./tools
  python fetch_upstream.py fetch --category network --dest ./tools --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "assets" / "upstream-catalog.json"
UA = "reverse-engineering-arsenal/1.0 (authorized security research)"


def load_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def select_sources(catalog: dict, ids: list[str], category: str | None) -> list[dict]:
    sources = catalog["sources"]
    if ids:
        wanted = {item.lower() for item in ids}
        chosen = [s for s in sources if s["id"].lower() in wanted or s["name"].lower() in wanted]
        missing = wanted - {s["id"].lower() for s in chosen} - {s["name"].lower() for s in chosen}
        if missing:
            raise SystemExit("unknown source id(s): " + ", ".join(sorted(missing)))
        return chosen
    if category:
        chosen = [s for s in sources if s["category"] == category]
        if not chosen:
            raise SystemExit(f"no sources in category {category!r}")
        return chosen
    return sources


def cmd_list(catalog: dict, args: argparse.Namespace) -> int:
    sources = select_sources(catalog, [], args.category)
    if args.json:
        print(json.dumps(sources, indent=2, ensure_ascii=False))
        return 0
    current = None
    for source in sources:
        if source["category"] != current:
            current = source["category"]
            print(f"\n[{current}] {catalog['categories'].get(current, '')}")
        status = f" ({source['status']})" if source.get("status") else ""
        print(f"  {source['id']:<32} {source['name']}{status}")
        print(f"  {'':<32} {source['url']}")
        print(f"  {'':<32} capabilities: {', '.join(source['capabilities'][:5])}{'...' if len(source['capabilities']) > 5 else ''}")
    print(f"\n{len(sources)} sources. Reference: {sources[0]['ref'] if sources else '-'}")
    return 0


def probe(url: str) -> tuple[int | None, str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, str(exc)


def cmd_check(catalog: dict, args: argparse.Namespace) -> int:
    sources = select_sources(catalog, args.ids, args.category)
    if args.limit:
        sources = sources[: args.limit]
    failures = 0
    for source in sources:
        url = source.get("repo") or source["url"]
        if not url.startswith("http"):
            print(f"SKIP {source['id']:<32} (no URL)")
            continue
        status, detail = probe(url)
        if status and status < 400:
            print(f"OK   {source['id']:<32} {status} {url}")
        elif source.get("status") == "deleted-upstream":
            print(f"KNOWN {source['id']:<31} {status or 'ERR'} {url} (upstream deleted)")
            if source.get("alternative"):
                print(f"      preserved via: {source['alternative']}")
        else:
            failures += 1
            print(f"FAIL {source['id']:<32} {status or 'ERR'} {url} :: {detail[:120]}")
            if source.get("alternative"):
                print(f"     alternative: {source['alternative']}")
            if source.get("status"):
                print(f"     status: {source['status']}")
    print(f"\nchecked={len(sources)} failures={failures}")
    return 0 if failures == 0 else 1


def clone_url(source: dict) -> str | None:
    url = source.get("repo") or source.get("url", "")
    if url.startswith("https://github.com/") and url.count("/") >= 4:
        return url
    return None


def cmd_fetch(catalog: dict, args: argparse.Namespace) -> int:
    sources = select_sources(catalog, args.ids, args.category)
    dest = Path(args.dest).resolve()
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    planned = 0
    skipped = 0
    for source in sources:
        url = clone_url(source)
        if not url:
            print(f"SKIP {source['id']}: no git URL (install manually: {source['install']})")
            skipped += 1
            continue
        target = dest / source["id"]
        if target.exists():
            print(f"SKIP {source['id']}: {target} already exists")
            skipped += 1
            continue
        command = ["git", "clone", "--depth", "1", "--single-branch"]
        if args.ref:
            command += ["--branch", args.ref]
        command += [url, str(target)]
        print(("DRY  " if args.dry_run else "RUN  ") + " ".join(command))
        planned += 1
        if not args.dry_run:
            try:
                subprocess.run(command, check=True)
                print(f"OK   {source['id']} -> {target}")
            except subprocess.CalledProcessError as exc:
                print(f"FAIL {source['id']}: git exited {exc.returncode}", file=sys.stderr)
                return 1
    print(f"\nplanned={planned} skipped={skipped} dest={dest}")
    if planned and not args.dry_run:
        print("Each repository keeps its own license. Review it before redistribution.")
    return 0


def main() -> int:
    catalog = load_catalog()
    parser = argparse.ArgumentParser(description="Browse/check/fetch the merged upstream catalog.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list catalogued sources")
    p_list.add_argument("--category", choices=sorted(catalog["categories"]))
    p_list.add_argument("--json", action="store_true")

    p_check = sub.add_parser("check", help="HEAD-check upstream URLs")
    p_check.add_argument("ids", nargs="*")
    p_check.add_argument("--category", choices=sorted(catalog["categories"]))
    p_check.add_argument("--limit", type=int, default=0)

    p_fetch = sub.add_parser("fetch", help="shallow-clone sources")
    p_fetch.add_argument("ids", nargs="*")
    p_fetch.add_argument("--category", choices=sorted(catalog["categories"]))
    p_fetch.add_argument("--dest", default="./upstream")
    p_fetch.add_argument("--ref")
    p_fetch.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.command == "list":
        return cmd_list(catalog, args)
    if args.command == "check":
        return cmd_check(catalog, args)
    if args.command == "fetch":
        return cmd_fetch(catalog, args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
