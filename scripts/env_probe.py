#!/usr/bin/env python3
"""Probe the local reverse-engineering toolchain and print actionable install hints.

Examples:
  python env_probe.py
  python env_probe.py --json
  python env_probe.py --category core
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# name, category, executable, version args, install hint, required-for
TOOLS = [
    ("node", "core", "node", ["--version"], "https://nodejs.org/ (>= 20)", "JS tooling, CDP clients, asar"),
    ("npm", "core", "npm", ["--version"], "ships with Node.js", "package installs"),
    ("npx", "core", "npx", ["--version"], "ships with Node.js", "one-shot CLIs"),
    ("python", "core", "python", ["--version"], "https://www.python.org/ (>= 3.10)", "helper scripts"),
    ("pip", "core", "pip", ["--version"], "python -m ensurepip --upgrade", "Python packages"),
    ("git", "core", "git", ["--version"], "https://git-scm.com/", "fetching upstream tools"),
    ("curl", "core", "curl", ["--version"], "built into Windows 10+ / apt install curl", "HTTP evidence capture"),
    ("java", "binary", "java", ["-version"], "JDK 21/25 for Ghidra: https://adoptium.net/", "Ghidra"),
    ("adb", "mobile", "adb", ["version"], "Android platform-tools", "Android capture / install"),
    ("frida", "mobile", "frida", ["--version"], "pip install frida-tools", "dynamic instrumentation"),
    ("frida-ps", "mobile", "frida-ps", ["--version"], "pip install frida-tools", "process enumeration"),
    ("mitmdump", "network", "mitmdump", ["--version"], "pip install mitmproxy", "scriptable capture"),
    ("mitmproxy", "network", "mitmproxy", ["--version"], "pip install mitmproxy", "interactive capture"),
    ("mitmweb", "network", "mitmweb", ["--version"], "pip install mitmproxy", "web capture UI"),
    ("tshark", "network", "tshark", ["--version"], "Wireshark / tshark", "pcap analysis"),
    ("strings", "binary", "strings", ["--version"], "binutils (WSL/Sysinternals on Windows)", "string triage"),
    ("file", "binary", "file", ["--version"], "WSL / Git Bash / file(1)", "file identification"),
    ("readelf", "binary", "readelf", ["--version"], "binutils (WSL/Linux)", "ELF analysis"),
    ("objdump", "binary", "objdump", ["--version"], "binutils (WSL/Linux)", "disassembly"),
    ("7z", "core", "7z", ["i"], "7-Zip", "archive extraction"),
    ("unzip", "core", "unzip", ["-v"], "unzip package / 7-Zip", "archive extraction"),
    ("r2", "binary", "r2", ["-v"], "https://radare.org/", "binary analysis"),
    ("rizin", "binary", "rizin", ["-v"], "https://rizin.re/", "binary analysis"),
    ("gdb", "binary", "gdb", ["--version"], "WSL / mingw / gdb", "ELF debugging"),
    ("lldb", "binary", "lldb", ["--version"], "LLVM / Xcode", "Mach-O debugging"),
    ("node-gyp", "binary", "node-gyp", ["--version"], "npm install -g node-gyp", "native module rebuilds"),
    ("ghidraRun", "binary", "ghidraRun", [], "Ghidra release + JDK 25", "decompilation GUI"),
    ("analyzeHeadless", "binary", "analyzeHeadless", [], "add Ghidra support/ to PATH", "headless decompilation"),
    ("x64dbg", "binary", "x64dbg", [], "https://x64dbg.com/", "Windows debugging"),
    ("diec", "binary", "diec", ["--help"], "https://github.com/horsicq/Detect-It-Easy", "packer/protector identification"),
    ("jadx", "mobile", "jadx", ["--version"], "https://github.com/skylot/jadx", "APK decompilation"),
    ("apktool", "mobile", "apktool", ["--version"], "https://apktool.org/", "APK decode/rebuild"),
    ("apksigner", "mobile", "apksigner", ["--version"], "Android build-tools", "APK signing"),
    ("baksmali", "mobile", "baksmali", ["--version"], "smali/baksmali", "DEX to smali"),
    ("smali", "mobile", "smali", ["--version"], "smali/baksmali", "smali to DEX"),
    ("d2j-dex2jar", "mobile", "d2j-dex2jar", ["--help"], "https://github.com/pxb1988/dex2jar", "DEX to JAR"),
    ("objection", "mobile", "objection", ["version"], "pip install objection", "Frida-based mobile testing"),
    ("playwright", "web", "playwright", ["--version"], "npm i -g playwright / pip install playwright", "browser automation"),
    ("chrome", "web", "chrome", ["--version"], "Google Chrome", "CDP / js-reverse-mcp"),
    ("firefox", "web", "firefox", ["--version"], "Mozilla Firefox", "ruyipage / Firefox-Reverse"),
    ("code", "electron", "code", ["--version"], "VS Code (often an Electron test target)", "Electron target"),
]

PY_MODULES = [
    ("frida", "dynamic instrumentation", "pip install frida"),
    ("mitmproxy", "proxy addon development", "pip install mitmproxy"),
    ("pefile", "PE parsing", "pip install pefile"),
    ("capstone", "disassembly", "pip install capstone"),
    ("requests", "HTTP capture scripts", "pip install requests"),
    ("ruyipage", "Firefox BiDi automation", "pip install ruyipage"),
    ("pycryptodome", "crypto reproduction", "pip install pycryptodome"),
]

APP_HINTS = [
    ("Qoder (Electron)", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Qoder", "resources/app.asar"),
    ("VS Code (Electron)", Path("C:/Program Files/Microsoft VS Code"), "resources/app.asar"),
    ("User VS Code (Electron)", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code", "resources/app.asar"),
    ("Google Chrome", Path("C:/Program Files/Google/Chrome/Application"), "chrome.exe"),
    ("Google Chrome (x86)", Path("C:/Program Files (x86)/Google/Chrome/Application"), "chrome.exe"),
    ("Microsoft Edge", Path("C:/Program Files (x86)/Microsoft/Edge/Application"), "msedge.exe"),
    ("Mozilla Firefox", Path("C:/Program Files/Mozilla Firefox"), "firefox.exe"),
    ("Ghidra", Path("C:/Program Files/ghidra"), "support/analyzeHeadless.bat"),
    ("Ghidra (Tools)", Path("C:/Tools/ghidra"), "support/analyzeHeadless.bat"),
    ("x64dbg", Path("C:/Tools/x64dbg"), "release/x64/x64dbg.exe"),
    ("Android SDK", Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk", "platform-tools/adb.exe"),
]


def version_of(exe: str, args: list[str]) -> str:
    path = shutil.which(exe)
    if not path:
        return ""
    if not args:
        return "present"
    try:
        proc = subprocess.run([path, *args], capture_output=True, text=True, timeout=8,
                              errors="ignore", shell=False)
        text = (proc.stdout or "") + (proc.stderr or "")
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first[:120]
    except (OSError, subprocess.SubprocessError):
        return "present"


def which(exe: str) -> str | None:
    return shutil.which(exe)


def collect() -> dict:
    rows = []
    for name, category, exe, args, hint, purpose in TOOLS:
        path = which(exe)
        rows.append({
            "name": name,
            "category": category,
            "found": bool(path),
            "path": path,
            "version": version_of(exe, args) if path else "",
            "install": hint,
            "purpose": purpose,
        })
    modules = []
    for name, purpose, hint in PY_MODULES:
        modules.append({
            "name": name,
            "found": importlib.util.find_spec(name) is not None,
            "purpose": purpose,
            "install": hint,
        })
    apps = []
    for name, root, marker in APP_HINTS:
        candidate = root / marker
        apps.append({"name": name, "root": str(root), "found": candidate.exists(), "marker": str(candidate)})
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
        "tools": rows,
        "python_modules": modules,
        "apps": apps,
    }


def print_text(data: dict, category: str | None) -> None:
    print("REA environment probe")
    print(f"OS: {data['os']}")
    print(f"Python: {data['python']}")
    print("")
    print(f"{'TOOL':<16} {'STATUS':<8} {'VERSION / PATH'}")
    print("-" * 78)
    for row in data["tools"]:
        if category and row["category"] != category:
            continue
        status = "OK" if row["found"] else "MISSING"
        detail = row["version"] if row["found"] else row["install"]
        print(f"{row['name']:<16} {status:<8} {detail[:56]}")
    print("")
    print("PYTHON MODULES")
    print("-" * 78)
    for row in data["python_modules"]:
        print(f"{row['name']:<16} {'OK' if row['found'] else 'MISSING':<8} {row['purpose'] if row['found'] else row['install']}")
    print("")
    print("KNOWN APP / TOOLCHAIN PATHS")
    print("-" * 78)
    for row in data["apps"]:
        print(f"{row['name']:<28} {'OK' if row['found'] else '-':<3} {row['marker']}")
    missing_core = [r["name"] for r in data["tools"] if r["category"] == "core" and not r["found"]]
    if missing_core:
        print("")
        print("Missing core tools: " + ", ".join(missing_core))
        print("Install Node.js, Python, Git, and 7-Zip first; domain tools can be added on demand.")
    else:
        print("")
        print("Core toolchain is ready. Add domain tools on demand and verify with --category.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe local RE toolchain.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--category", help="core|network|binary|mobile|web|electron")
    args = parser.parse_args()
    data = collect()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_text(data, args.category)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
