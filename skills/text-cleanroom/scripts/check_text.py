#!/usr/bin/env python3
"""Read-only, standard-library text checks; not an AI/watermark detector."""

import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import unicodedata

MAX_BYTES = 1024 * 1024
MAX_ITEMS = 100
MAX_DIFF_LINES = 200
NUMBER = re.compile(r"[-+\u2212]?\d+(?:[.,:/-]\d+)*")
URL = re.compile(r'https?://[^\s<>"`]+', re.IGNORECASE)


def read_text(path):
    source = Path(path)
    if source.suffix.lower() not in {".txt", ".md", ".markdown"}:
        raise ValueError("expected .txt, .md or .markdown input")
    if not stat.S_ISREG(source.stat().st_mode):
        raise ValueError("expected a regular file")
    with source.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds the 1 MiB limit")
    text = raw.decode("utf-8")
    if "\x00" in text:
        raise ValueError("NUL-containing input is not supported")
    return text, hashlib.sha256(raw).hexdigest()


def inspect_text(text):
    items = []
    count = 0
    line, column = 1, 1
    for char in text:
        category = unicodedata.category(char)
        if category in {"Cf", "Zl", "Zp"} or (
            category == "Cc" and char not in "\r\n\t"
        ) or char in "\u00a0\u202f":
            count += 1
            if len(items) < MAX_ITEMS:
                items.append({
                    "line": line, "column": column,
                    "codepoint": f"U+{ord(char):04X}",
                    "name": unicodedata.name(char, "UNNAMED"),
                    "category": category,
                })
        if char == "\n":
            line, column = line + 1, 1
        else:
            column += 1
    return {
        "characters_for_contextual_review": items,
        "occurrences": count,
        "omitted_occurrences": count - len(items),
        "interpretation": "These characters may be legitimate. Nothing was removed.",
    }


def token_delta(pattern, before, after):
    original = Counter(pattern.findall(before))
    candidate = Counter(pattern.findall(after))
    missing, added = original - candidate, candidate - original
    return {
        "missing": dict(list(missing.items())[:MAX_ITEMS]),
        "added": dict(list(added.items())[:MAX_ITEMS]),
        "omitted_unique_tokens": max(0, len(missing) - MAX_ITEMS)
        + max(0, len(added) - MAX_ITEMS),
        "changed": original != candidate,
    }


def compare_text(before, after, protected):
    numbers = token_delta(NUMBER, before, after)
    urls = token_delta(URL, before, after)
    phrases = [
        {"text": phrase, "before": before.count(phrase), "after": after.count(phrase)}
        for phrase in dict.fromkeys(protected)
        if before.count(phrase) != after.count(phrase)
    ]
    differences = bool(numbers["changed"] or urls["changed"] or phrases)
    diff = list(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="original", tofile="candidate",
    ))
    return {
        "status": "requires_review" if differences else "no_heuristic_differences",
        "numbers": numbers, "urls": urls, "protected_phrase_changes": phrases,
        "candidate_inspection": inspect_text(after),
        "diff": diff[:MAX_DIFF_LINES],
        "omitted_diff_lines": max(0, len(diff) - MAX_DIFF_LINES),
        "semantic_equivalence": "not_verified",
        "watermark_status": "not_verified",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("original")
    compare = sub.add_parser("compare")
    compare.add_argument("original")
    compare.add_argument("candidate")
    compare.add_argument("--protect", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        before, original_hash = read_text(args.original)
        if args.command == "inspect":
            report = inspect_text(before)
            report["watermark_status"] = "not_verified"
        else:
            if any(not phrase for phrase in args.protect):
                raise ValueError("protected phrases must not be empty")
            after, candidate_hash = read_text(args.candidate)
            report = compare_text(before, after, args.protect)
            report["candidate_sha256"] = candidate_hash
        report["original_sha256"] = original_hash
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return int(report.get("status") == "requires_review")


if __name__ == "__main__":
    sys.exit(main())
