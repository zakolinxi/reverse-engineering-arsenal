#!/usr/bin/env python3
"""Static triage for JavaScript reverse-engineering targets.

Scans JS files for obfuscation, JSVMP, crypto, WebAssembly, API endpoints,
signature-related parameters and embedded secrets. Produces a Markdown or JSON
report that tells you which dynamic tool to reach for next.

Examples:
  python js_triage.py app.js
  python js_triage.py unpacked/ --out triage.md
  python js_triage.py bundle.js --json --top 20
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

JS_EXTENSIONS = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"}

SIGNALS = [
    ("obfuscation", "hex identifiers (_0x...)", re.compile(r"\b_0x[0-9a-fA-F]{4,}\b"), 3),
    ("obfuscation", "eval()", re.compile(r"\beval\s*\("), 2),
    ("obfuscation", "new Function()", re.compile(r"\bnew\s+Function\s*\("), 2),
    ("obfuscation", "String.fromCharCode", re.compile(r"String\.fromCharCode"), 2),
    ("obfuscation", "atob()", re.compile(r"\batob\s*\("), 1),
    ("obfuscation", "debugger statement", re.compile(r"\bdebugger\b"), 1),
    ("obfuscation", "self-defending / constructor trick", re.compile(r"constructor\s*\(\s*['\"]return|arguments\.callee"), 2),
    ("obfuscation", "infinite loop", re.compile(r"while\s*\(\s*(?:true|1|!!\s*\[\s*\])\s*\)"), 1),
    ("obfuscation", "control-flow switch", re.compile(r"switch\s*\(\s*[A-Za-z_$][\w$]*\s*\)"), 1),
    ("obfuscation", "case labels", re.compile(r"\bcase\s+[-+]?\d+\s*:"), 0),
    ("obfuscation", "hex escapes", re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}"), 1),
    ("jsvmp", "VM program counter", re.compile(r"\b(?:vm_?)?pc\b\s*(?:\+\+|--|[+\-*/]?=)"), 2),
    ("jsvmp", "bytecode array", re.compile(r"\b(?:bytecode|opcode|opcodes|code\s*=|program)\b"), 1),
    ("wasm", "WebAssembly", re.compile(r"\bWebAssembly\b|\.wasm\b"), 3),
    ("crypto", "CryptoJS / crypto-js", re.compile(r"\bCryptoJS\b|crypto-js"), 3),
    ("crypto", "JSEncrypt", re.compile(r"\bJSEncrypt\b"), 3),
    ("crypto", "node-forge", re.compile(r"\bnode-forge\b|\bforge\.\w+"), 2),
    ("crypto", "WebCrypto SubtleCrypto", re.compile(r"\bcrypto\.subtle\b|\bsubtle\.(?:digest|encrypt|decrypt|sign|verify|deriveBits|importKey)\b"), 3),
    ("crypto", "AES", re.compile(r"\bAES\b|\bAes\b"), 2),
    ("crypto", "DES / 3DES", re.compile(r"\b(?:DES|TripleDES|3DES)\b"), 1),
    ("crypto", "RSA", re.compile(r"\bRSA\b"), 2),
    ("crypto", "MD5", re.compile(r"\bMD5\b|\bmd5sum\b"), 2),
    ("crypto", "SHA family", re.compile(r"\bSHA(?:-?1|-?224|-?256|-?384|-?512)\b"), 2),
    ("crypto", "HMAC", re.compile(r"\bHMAC\b|\bHmac\b"), 2),
    ("crypto", "SM2 / SM4", re.compile(r"\bSM[24]\b"), 2),
    ("crypto", "RC4 / XXTEA", re.compile(r"\b(?:RC4|XXTEA)\b"), 1),
    ("crypto", "PBKDF2 / bcrypt / scrypt", re.compile(r"\b(?:PBKDF2|bcrypt|scrypt|argon2)\b", re.I), 1),
    ("crypto", "WordArray / CipherParams", re.compile(r"\b(?:WordArray|CipherParams)\b"), 1),
    ("network", "URL literal", re.compile(r"https?://[^\s'\"<>`\\]+"), 0),
    ("network", "API path literal", re.compile(r"['\"`](/(?:api|v\d|graphql|rest|openapi)/[^'\"`\s]{1,200})['\"`]"), 0),
    ("network", "signature parameter", re.compile(r"\b(?:sign|signature|sig|nonce|timestamp|_ts|token|deviceId|device_id|fingerprint)\b|\bX-[A-Za-z0-9-]{2,}\b", re.I), 0),
    ("secrets", "PEM private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), 5),
    ("secrets", "AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 4),
    ("secrets", "long base64-like literal", re.compile(r"['\"][A-Za-z0-9+/]{40,}={0,2}['\"]"), 1),
]

SPECIAL = {
    "case_labels": re.compile(r"\bcase\s+[-+]?\d+\s*:"),
    "call_count_decoder": re.compile(r"\b_0x[0-9a-fA-F]{4,}\s*=\s*function\b|\bfunction\s+_0x[0-9a-fA-F]{4,}\b"),
    "string_array": re.compile(r"\[\s*(?:['\"][^'\"]{1,200}['\"]\s*,\s*){20,}"),
}

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".turbo", "coverage", ".cache"}


def gather_files(paths: list[str], include_vendor: bool) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            for file in path.rglob("*"):
                if not file.is_file() or file.suffix.lower() not in JS_EXTENSIONS:
                    continue
                if not include_vendor and any(part in SKIP_DIRS for part in file.parts):
                    continue
                found.append(file)
        else:
            matches = list(Path(".").glob(raw))
            found.extend(p for p in matches if p.is_file())
    seen = set()
    unique = []
    for file in found:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(file)
    return unique


def snippet(text: str, start: int, end: int, width: int = 110) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    value = text[left:right].replace("\n", " ").replace("\r", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return ("..." if left else "") + value + ("..." if right < len(text) else "")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_file(file: Path, max_bytes: int, per_signal: int) -> dict:
    with file.open("rb") as handle:
        data = handle.read(max_bytes)
    if b"\x00" in data[:4096]:
        return {"file": str(file), "skipped": "binary"}
    text = data.decode("utf-8", errors="ignore")
    result = {
        "file": str(file),
        "bytes_scanned": len(data),
        "truncated": file.stat().st_size > len(data),
        "signals": OrderedDict(),
        "endpoints": [],
        "api_paths": [],
        "parameters": [],
        "likely": [],
    }
    counts: dict[str, int] = {}
    for category, name, pattern, weight in SIGNALS:
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        if name == "long base64-like literal":
            matches = [
                m for m in matches
                if "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" not in m.group(0)
            ]
        if not matches:
            continue
        counts[name] = len(matches)
        samples = []
        for match in matches[:per_signal]:
            value = match.group(0)
            if len(value) > 240:
                value = value[:240] + "..."
            samples.append({"line": line_of(text, match.start()), "value": value})
        result["signals"].setdefault(category, []).append({
            "name": name,
            "count": len(matches),
            "weight": weight,
            "samples": samples,
        })
        if name == "URL literal":
            for match in matches:
                url = match.group(0).rstrip(").,;'\"")
                if url not in result["endpoints"] and len(result["endpoints"]) < 40:
                    result["endpoints"].append(url)
        elif name == "API path literal":
            for match in matches:
                api = match.group(1)
                if api not in result["api_paths"] and len(result["api_paths"]) < 40:
                    result["api_paths"].append(api)
        elif name == "signature parameter":
            for match in matches:
                param = match.group(0)
                if param not in result["parameters"] and len(result["parameters"]) < 40:
                    result["parameters"].append(param)

    case_count = len(SPECIAL["case_labels"].findall(text))
    decoder_count = len(SPECIAL["call_count_decoder"].findall(text))
    has_string_array = bool(SPECIAL["string_array"].search(text))
    hex_ids = counts.get("hex identifiers (_0x...)", 0)
    has_eval = "eval()" in counts
    has_infinite = "infinite loop" in counts
    has_pc = "VM program counter" in counts
    has_wasm = "WebAssembly" in counts
    crypto_hits = len(result["signals"].get("crypto", []))

    if hex_ids >= 20 or (has_eval and has_string_array):
        result["likely"].append("obfuscated (string-array / hex identifier pattern)")
    if (case_count >= 60 and (has_pc or has_infinite)) or (has_pc and case_count >= 30):
        result["likely"].append("JSVMP / custom bytecode VM")
    if has_wasm:
        result["likely"].append("WASM-backed logic")
    if crypto_hits >= 3:
        result["likely"].append("crypto-heavy")
    if decoder_count:
        result["likely"].append("decoder-function pattern")
    if result["signals"].get("secrets"):
        result["likely"].append("possible hardcoded secret")

    score = 0
    for items in result["signals"].values():
        for item in items:
            score += min(item["count"], 5) * item["weight"]
    score += min(case_count, 100) * 0.05
    result["score"] = round(score, 1)
    result["case_labels"] = case_count
    result["has_string_array"] = has_string_array
    return result


def md_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("`", "\\`").replace("|", "\\|")


def render_markdown(results: list[dict], top: int) -> str:
    total_files = len([r for r in results if "skipped" not in r])
    lines = [
        "# JavaScript Triage Report",
        "",
        f"- Files scanned: **{total_files}**",
        f"- Total bytes: **{sum(r.get('bytes_scanned', 0) for r in results):,}**",
        "",
    ]
    verdicts = []
    for result in results:
        if "skipped" in result:
            continue
        verdicts.extend(result.get("likely", []))
    if verdicts:
        lines += ["## Verdict", ""]
        for verdict in sorted(set(verdicts)):
            lines.append(f"- {verdict}")
        lines.append("")

    lines += ["## Ranked files", "", "| File | Score | Bytes | Likely |", "| --- | ---: | ---: | --- |"]
    ranked = sorted((r for r in results if "skipped" not in r), key=lambda r: r.get("score", 0), reverse=True)
    for result in ranked[:top]:
        likely = "; ".join(result.get("likely", [])) or "-"
        lines.append(f"| `{result['file']}` | {result.get('score', 0)} | {result.get('bytes_scanned', 0):,} | {likely} |")
    lines.append("")

    for result in ranked[:top]:
        if not result.get("signals"):
            continue
        lines += [f"### `{result['file']}`", ""]
        if result.get("truncated"):
            lines.append(f"> Scanned only the first {result['bytes_scanned']:,} bytes.")
            lines.append("")
        lines += ["| Category | Signal | Count | Evidence |", "| --- | --- | ---: | --- |"]
        for category, items in result["signals"].items():
            for item in items:
                evidence = "<br>".join(
                    f"L{s['line']}: `{md_escape(s['value'][:100])}`" for s in item["samples"][:2]
                ) or "-"
                lines.append(f"| {category} | {item['name']} | {item['count']} | {evidence} |")
        lines.append("")
        if result.get("api_paths"):
            lines += ["API paths:", "", *[f"- `{md_escape(p)}`" for p in result["api_paths"][:15]], ""]
        if result.get("endpoints"):
            lines += ["Endpoints:", "", *[f"- {md_escape(u)}" for u in result["endpoints"][:15]], ""]
        if result.get("parameters"):
            lines += ["Signature-related names:", "", ", ".join(f"`{p}`" for p in result["parameters"][:20]), ""]

    lines += [
        "## Suggested next steps",
        "",
        "- Obfuscated: run `npx deob` (kuizuo/js-deobfuscator) or the AST workflow in `references/js-web-reverse.md`.",
        "- JSVMP / WASM: capture runtime evidence with RuyiTrace or js-reverse-mcp before attempting reconstruction.",
        "- Crypto-heavy: set a breakpoint on the signature call, dump inputs/outputs, then rebuild in Node/Python.",
        "- Endpoints and parameter names: use them as breakpoint and hook anchors.",
        "- Always verify a reconstruction against at least five real responses from an authorized target.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Static triage for JavaScript reverse engineering.")
    parser.add_argument("paths", nargs="+", help="JS files, directories, or globs")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument("--out", type=Path, help="write report to this file")
    parser.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024, help="bytes per file (default 5 MiB)")
    parser.add_argument("--top", type=int, default=10, help="ranked files in the report")
    parser.add_argument("--per-signal", type=int, default=3, help="samples per signal")
    parser.add_argument("--include-vendor", action="store_true", help="do not skip node_modules/dist/build")
    args = parser.parse_args()

    files = gather_files(args.paths, args.include_vendor)
    if not files:
        print("no JavaScript files found", file=sys.stderr)
        return 2
    results = [scan_file(file, args.max_bytes, args.per_signal) for file in files]
    if args.json:
        output = json.dumps({"files": results}, indent=2, ensure_ascii=False)
    else:
        output = render_markdown(results, args.top)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        verdict = sorted({v for r in results for v in r.get("likely", [])})
        print(f"scanned={len(files)} report={args.out} verdict={'; '.join(verdict) or 'no strong signals'}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
