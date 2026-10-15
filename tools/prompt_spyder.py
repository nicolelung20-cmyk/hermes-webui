#!/usr/bin/env python3
"""Prompt Spyder: local, read-only prompt and instruction risk scanner.

Scans explicitly supplied text files. It never executes scanned content, follows
symlinks, reads environment files by default, or sends data over the network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES = [
    ("prompt_injection", "high", re.compile(
        r"\b(ignore|disregard|override|bypass)\b.{0,70}\b(previous|prior|above|system|developer|safety|instructions?|rules?)\b",
        re.I)),
    ("secret_exfiltration", "critical", re.compile(
        r"\b(reveal|print|dump|exfiltrate|send|upload|expose)\b.{0,60}\b(api[_ -]?keys?|tokens?|passwords?|credentials?|secrets?|\.env)\b",
        re.I)),
    ("authority_impersonation", "high", re.compile(
        r"\b(you are now|new system prompt|system override|developer message|admin override)\b",
        re.I)),
    ("unsafe_tool_action", "high", re.compile(
        r"\b(disable|remove|turn off)\b.{0,60}\b(authentication|authorization|rls|logging|audit|safety checks?)\b",
        re.I)),
    ("untrusted_content_execution", "high", re.compile(
        r"\b(execute|run|eval|interpret)\b.{0,50}\b(untrusted|user[- ]supplied|external)\b.{0,35}\b(code|command|prompt|content|input)\b",
        re.I)),
]
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,})\b"),
]
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".next", "dist", "build"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "auth.json", "credentials.json"}


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda m: (m.group(1) + "=[REDACTED]") if m.lastindex and m.lastindex >= 2 else "[REDACTED_SECRET]", text)
    return text


def scan_text(text: str, source: str = "<input>") -> list[dict]:
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule, severity, pattern in RULES:
            if pattern.search(line):
                findings.append({
                    "source": source,
                    "line": line_no,
                    "rule": rule,
                    "severity": severity,
                    "evidence": redact(line.strip())[:240],
                    "recommendation": "Treat this as untrusted content; require explicit policy checks before tool use or disclosure.",
                })
    return findings


def iter_files(paths: list[Path], include_sensitive: bool = False):
    seen = set()
    for path in paths:
        if path.is_symlink():
            continue
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = (p for p in path.rglob("*") if p.is_file() and not p.is_symlink()
                          and not any(part in SKIP_DIRS for part in p.parts))
        else:
            continue
        for file in candidates:
            resolved = file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if not include_sensitive and (file.name in SENSITIVE_NAMES or file.name.startswith(".env.")):
                continue
            if file.suffix.lower() not in {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".prompt", ".xml"}:
                continue
            yield file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--include-sensitive", action="store_true",
                        help="Allow explicitly supplied .env/auth/credential files (not recommended)")
    args = parser.parse_args(argv)
    findings = []
    scanned = []
    errors = []
    for file in iter_files([Path(p) for p in args.paths], args.include_sensitive):
        try:
            content = file.read_text(encoding="utf-8", errors="replace")
            scanned.append(str(file))
            findings.extend(scan_text(content, str(file)))
        except OSError as exc:
            errors.append({"source": str(file), "error": type(exc).__name__})
    report = {"tool": "prompt-spyder", "version": "0.1.0", "mode": "read-only",
              "scanned_files": len(scanned), "findings_count": len(findings),
              "findings": findings, "errors": errors,
              "note": "Heuristic findings require human review; absence of findings is not proof of safety."}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Prompt Spyder — scanned {len(scanned)} file(s); {len(findings)} finding(s)")
        for item in findings:
            print(f"[{item['severity'].upper()}] {item['source']}:{item['line']} {item['rule']}: {item['evidence']}")
        for item in errors:
            print(f"[ERROR] Could not read {item['source']} ({item['error']})")
        print(report["note"])
    return 1 if findings or errors else 0


if __name__ == "__main__":
    sys.exit(main())
