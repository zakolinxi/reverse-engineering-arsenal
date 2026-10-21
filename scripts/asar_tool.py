#!/usr/bin/env python3
"""Inspect and extract Electron ASAR archives with the Python standard library.

Commands:
  list <app.asar> [--json]
  info <app.asar> [--json]
  extract <app.asar> <dest> [--path SUBSTR] [--force] [--verify] [--symlinks]
  cat <app.asar> <internal/path>

ASAR layout (Chromium Pickle):
  bytes 0..3   uint32 pickle payload size (normally 4)
  bytes 4..7   uint32 header pickle size
  bytes 8..    header pickle: uint32 payload size + uint32 JSON length + JSON
  data start   = 8 + header pickle size
  file offset  relative to data start

Only run this on software you own or are authorized to inspect.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import struct
import sys
from pathlib import Path

CHUNK = 1024 * 1024


class AsarError(Exception):
    pass


def human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024.0
    return str(n)


def read_header(archive: Path) -> tuple[dict, int, int]:
    size = archive.stat().st_size
    if size < 16:
        raise AsarError("file is too small to be an ASAR archive")
    with archive.open("rb") as fh:
        head = fh.read(8)
        if len(head) != 8:
            raise AsarError("cannot read ASAR header size")
        payload_size, header_size = struct.unpack("<II", head)
        if payload_size != 4:
            raise AsarError(f"unexpected pickle header size {payload_size}; not an ASAR archive")
        if header_size < 4 or header_size > size - 8:
            raise AsarError(f"invalid ASAR header size {header_size}")
        hbuf = fh.read(header_size)
        if len(hbuf) != header_size:
            raise AsarError("truncated ASAR header")
    if len(hbuf) < 8:
        raise AsarError("truncated ASAR header pickle")
    header_payload, json_len = struct.unpack("<II", hbuf[:8])
    if json_len > len(hbuf) - 8:
        raise AsarError("ASAR header JSON length is out of bounds")
    raw = hbuf[8 : 8 + json_len]
    try:
        header = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AsarError(f"cannot parse ASAR header JSON: {exc}") from exc
    if not isinstance(header, dict) or not isinstance(header.get("files"), dict):
        raise AsarError("ASAR header has no files table")
    return header, header_size, 8 + header_size


def walk_entries(node: dict, prefix: str = ""):
    for name, entry in node.get("files", {}).items():
        if not isinstance(entry, dict):
            continue
        path = f"{prefix}{name}"
        if "files" in entry:
            yield from walk_entries(entry, path + "/")
        else:
            yield path, entry


def entry_size(entry: dict) -> int:
    try:
        return int(entry.get("size", 0))
    except (TypeError, ValueError):
        return 0


def is_unpacked(entry: dict) -> bool:
    return bool(entry.get("unpacked"))


def build_index(archive: Path) -> tuple[dict[str, dict], dict, int, int]:
    header, header_size, data_start = read_header(archive)
    entries = dict(walk_entries(header))
    return entries, header, header_size, data_start


def safe_rel(path: str) -> str:
    norm = posixpath.normpath(path.replace("\\", "/"))
    if norm in (".", "") or norm.startswith("../") or norm == ".." or norm.startswith("/"):
        raise AsarError(f"unsafe archive path: {path!r}")
    if len(norm) > 1 and norm[1] == ":":
        raise AsarError(f"absolute archive path: {path!r}")
    return norm


def resolve_link(path: str, entry: dict, entries: dict[str, dict]) -> str:
    target = posixpath.normpath(posixpath.join(posixpath.dirname(path), entry.get("link", "")))
    if target not in entries:
        raise AsarError(f"link target not found: {path} -> {target}")
    return target


def copy_entry(archive: Path, entry: dict, out: Path, data_start: int) -> None:
    size = entry_size(entry)
    offset = int(entry.get("offset", 0))
    archive_size = archive.stat().st_size
    if offset < 0 or size < 0 or data_start + offset + size > archive_size:
        raise AsarError(f"entry is outside archive bounds: offset={offset} size={size}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as src:
        src.seek(data_start + offset)
        remaining = size
        with out.open("wb") as dst:
            while remaining > 0:
                chunk = src.read(min(CHUNK, remaining))
                if not chunk:
                    raise AsarError("unexpected EOF while extracting entry")
                dst.write(chunk)
                remaining -= len(chunk)
    if entry.get("executable") and os.name != "nt":
        try:
            out.chmod(out.stat().st_mode | 0o111)
        except OSError:
            pass


def verify_sha256(path: Path, entry: dict) -> bool | None:
    integrity = entry.get("integrity") or {}
    expected = integrity.get("hash")
    if not expected:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == str(expected).lower()


def select_entries(entries: dict[str, dict], pattern: str | None) -> list[tuple[str, dict]]:
    items = sorted(entries.items())
    if not pattern:
        return items
    pat = pattern.replace("\\", "/")
    selected = []
    for path, entry in items:
        if pat in path or fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(posixpath.basename(path), pat):
            selected.append((path, entry))
    return selected


def extract(archive: Path, dest: Path, pattern: str | None, force: bool,
            verify: bool, symlinks: bool) -> int:
    entries, _, _, data_start = build_index(archive)
    chosen = select_entries(entries, pattern)
    if not chosen:
        print(f"no entries matched {pattern!r}", file=sys.stderr)
        return 2
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    extracted = 0
    failures = 0
    unpacked_root = Path(str(archive) + ".unpacked")
    for path, entry in chosen:
        rel = safe_rel(path)
        target = (dest / Path(*rel.split("/"))).resolve()
        if not target.is_relative_to(root):
            print(f"SKIP unsafe path: {path}", file=sys.stderr)
            failures += 1
            continue
        try:
            if "link" in entry:
                link_target = resolve_link(path, entry, entries)
                target_entry = entries[link_target]
                actual = target
                if symlinks and os.name != "nt":
                    actual.parent.mkdir(parents=True, exist_ok=True)
                    if actual.exists() or actual.is_symlink():
                        if not force:
                            raise AsarError("destination exists (use --force)")
                        actual.unlink()
                    os.symlink(posixpath.relpath(link_target, posixpath.dirname(path)), actual)
                else:
                    if actual.exists() and not force:
                        raise AsarError("destination exists (use --force)")
                    if is_unpacked(target_entry):
                        unpacked = unpacked_root / Path(*safe_rel(link_target).split("/"))
                        if not unpacked.is_file():
                            raise AsarError(f"unpacked link target missing: {unpacked}")
                        actual.parent.mkdir(parents=True, exist_ok=True)
                        actual.write_bytes(unpacked.read_bytes())
                    else:
                        copy_entry(archive, target_entry, actual, data_start)
            elif is_unpacked(entry):
                unpacked = unpacked_root / Path(*rel.split("/"))
                if not unpacked.is_file():
                    raise AsarError(f"unpacked file missing next to archive: {unpacked}")
                if target.exists() and not force:
                    raise AsarError("destination exists (use --force)")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(unpacked.read_bytes())
            else:
                if target.exists() and not force:
                    raise AsarError("destination exists (use --force)")
                copy_entry(archive, entry, target, data_start)
            if verify and "link" not in entry:
                result = verify_sha256(target, entry)
                if result is False:
                    raise AsarError("SHA-256 integrity mismatch")
            extracted += 1
        except (OSError, AsarError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            failures += 1
    print(f"extracted={extracted} failed={failures} dest={dest}")
    return 0 if failures == 0 else 1


def cmd_list(archive: Path, as_json: bool) -> int:
    entries, header, header_size, data_start = build_index(archive)
    rows = []
    for path, entry in sorted(entries.items()):
        rows.append({
            "path": path,
            "size": entry_size(entry),
            "offset": entry.get("offset"),
            "unpacked": is_unpacked(entry),
            "link": entry.get("link"),
            "executable": bool(entry.get("executable")),
            "sha256": (entry.get("integrity") or {}).get("hash"),
        })
    if as_json:
        print(json.dumps({"archive": str(archive), "header_size": header_size,
                          "data_start": data_start, "count": len(rows), "files": rows},
                         indent=2, ensure_ascii=False))
        return 0
    for row in rows:
        flags = []
        if row["unpacked"]:
            flags.append("unpacked")
        if row["link"]:
            flags.append(f"link->{row['link']}")
        if row["executable"]:
            flags.append("exec")
        suffix = (" [" + ", ".join(flags) + "]") if flags else ""
        print(f"{human(row['size']):>10}  {row['path']}{suffix}")
    print(f"\n{len(rows)} files, header {human(header_size)}, data starts at {data_start}")
    return 0


def cmd_info(archive: Path, as_json: bool) -> int:
    entries, header, header_size, data_start = build_index(archive)
    total = sum(entry_size(e) for _, e in entries.items())
    unpacked = sum(1 for _, e in entries.items() if is_unpacked(e))
    links = sum(1 for _, e in entries.items() if "link" in e)
    integrity = sum(1 for _, e in entries.items() if (e.get("integrity") or {}).get("hash"))
    info = {
        "archive": str(archive),
        "archive_bytes": archive.stat().st_size,
        "header_bytes": header_size,
        "data_start": data_start,
        "files": len(entries),
        "unpacked_files": unpacked,
        "links": links,
        "files_with_integrity": integrity,
        "logical_bytes": total,
        "top_level": sorted(header.get("files", {}).keys()),
    }
    if as_json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        for key, value in info.items():
            print(f"{key}: {value}")
    return 0


def cmd_cat(archive: Path, internal: str) -> int:
    entries, _, _, data_start = build_index(archive)
    norm = safe_rel(internal)
    if norm not in entries:
        print(f"not found: {internal}", file=sys.stderr)
        return 2
    entry = entries[norm]
    if "link" in entry:
        entry = entries[resolve_link(norm, entry, entries)]
    if is_unpacked(entry):
        path = Path(str(archive) + ".unpacked") / Path(*norm.split("/"))
        sys.stdout.buffer.write(path.read_bytes())
        return 0
    size = entry_size(entry)
    offset = int(entry.get("offset", 0))
    with archive.open("rb") as fh:
        fh.seek(data_start + offset)
        remaining = size
        while remaining:
            chunk = fh.read(min(CHUNK, remaining))
            if not chunk:
                raise AsarError("unexpected EOF")
            sys.stdout.buffer.write(chunk)
            remaining -= len(chunk)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and extract Electron ASAR archives (stdlib only).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list archive entries")
    p_list.add_argument("archive", type=Path)
    p_list.add_argument("--json", action="store_true")

    p_info = sub.add_parser("info", help="show archive summary")
    p_info.add_argument("archive", type=Path)
    p_info.add_argument("--json", action="store_true")

    p_ext = sub.add_parser("extract", help="extract files")
    p_ext.add_argument("archive", type=Path)
    p_ext.add_argument("dest", type=Path)
    p_ext.add_argument("--path", help="substring, glob, or basename filter")
    p_ext.add_argument("--force", action="store_true")
    p_ext.add_argument("--verify", action="store_true", help="verify SHA-256 when header provides it")
    p_ext.add_argument("--symlinks", action="store_true", help="recreate links as symlinks on POSIX")

    p_cat = sub.add_parser("cat", help="write one entry to stdout")
    p_cat.add_argument("archive", type=Path)
    p_cat.add_argument("internal")

    args = parser.parse_args()
    try:
        if args.command == "list":
            return cmd_list(args.archive, args.json)
        if args.command == "info":
            return cmd_info(args.archive, args.json)
        if args.command == "extract":
            return extract(args.archive, args.dest, args.path, args.force, args.verify, args.symlinks)
        if args.command == "cat":
            return cmd_cat(args.archive, args.internal)
    except BrokenPipeError:
        # `asar_tool.py list ... | head` closes stdout early; exit quietly.
        try:
            sys.stdout.close()
        except OSError:
            pass
        return 0
    except (OSError, AsarError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
