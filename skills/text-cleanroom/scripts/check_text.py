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
NUMBER = re.compile(r"[-+\u2212]?(?:\d+(?:[.,:/-]\d+)*|[.,]\d+)(?:[eE][-+]?\d+)?")
URL = re.compile(r'https?://[^\s<>"`]+', re.IGNORECASE)
BLANKS = frozenset("\u034f\u115f\u1160\u3164\uffa0\u2800")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)$")


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


def needs_unicode_review(char):
    category, codepoint = unicodedata.category(char), ord(char)
    return (
        category in {"Cf", "Zl", "Zp"}
        or (category == "Cc" and char not in "\r\n\t")
        or (category == "Zs" and char != " ")
        or 0xFE00 <= codepoint <= 0xFE0F
        or 0xE0100 <= codepoint <= 0xE01EF
        or char in BLANKS
    )


def inspect_text(text):
    items = []
    count = 0
    # Share splitlines semantics with the unified diff, including CRLF and NEL.
    for line, content in enumerate(text.splitlines(keepends=True), 1):
        for column, char in enumerate(content, 1):
            if needs_unicode_review(char):
                count += 1
                if len(items) < MAX_ITEMS:
                    items.append({
                        "line": line, "column": column,
                        "codepoint": f"U+{ord(char):04X}",
                        "name": unicodedata.name(char, "UNNAMED"),
                        "category": unicodedata.category(char),
                    })
    return {
        "characters_for_contextual_review": items,
        "occurrences": count,
        "omitted_occurrences": count - len(items),
        "interpretation": "These characters may be legitimate. Nothing was removed.",
    }


def counter_delta(original, candidate):
    missing, added = original - candidate, candidate - original
    return {
        "missing": dict(list(missing.items())[:MAX_ITEMS]),
        "added": dict(list(added.items())[:MAX_ITEMS]),
        "omitted_unique_tokens": max(0, len(missing) - MAX_ITEMS)
        + max(0, len(added) - MAX_ITEMS),
        "changed": original != candidate,
    }


def token_delta(pattern, before, after):
    return counter_delta(Counter(pattern.findall(before)), Counter(pattern.findall(after)))


def unicode_counts(text):
    return Counter(f"U+{ord(char):04X}" for char in text if needs_unicode_review(char))


def inline_code(text):
    """Extract exact spans with matching-length backtick runs, not rendered HTML."""
    runs = list(re.finditer(r"`+", text))
    next_same, latest = {}, {}
    for index in range(len(runs) - 1, -1, -1):
        width = len(runs[index].group())
        if width in latest:
            next_same[index] = latest[width]
        latest[width] = index
    index = 0
    while index < len(runs):
        start = runs[index].start()
        pos = start
        while pos and text[pos - 1] == "\\":
            pos -= 1
        if (start - pos) % 2 == 0 and index in next_same:
            closing = next_same[index]
            yield text[start:runs[closing].end()]
            index = closing + 1
        else:
            index += 1


def code_counts(text):
    """Conservative subset: top-level fences and inline spans outside fences."""
    regions, prose, block = Counter(), [], []
    fence_char, fence_width = None, 0
    for line in text.splitlines(keepends=True):
        match = FENCE.fullmatch(line.rstrip("\r\n"))
        if fence_char:
            block.append(line)
            if (match and match[1][0] == fence_char
                    and len(match[1]) >= fence_width and not match[2].strip(" \t")):
                regions["".join(block)] += 1
                block, fence_char = [], None
        elif match and not (match[1][0] == "`" and "`" in match[2]):
            regions.update(inline_code("".join(prose)))
            prose = []
            block, fence_char, fence_width = [line], match[1][0], len(match[1])
        else:
            prose.append(line)
    if block:  # An unclosed fence protects the remainder, rather than dropping it.
        regions["".join(block)] += 1
    regions.update(inline_code("".join(prose)))
    return regions


def compare_text(before, after, protected):
    numbers = token_delta(NUMBER, before, after)
    urls = token_delta(URL, before, after)
    unicode_changes = counter_delta(unicode_counts(before), unicode_counts(after))
    code = counter_delta(code_counts(before), code_counts(after))
    phrases = [
        {"text": phrase, "before": before.count(phrase), "after": after.count(phrase)}
        for phrase in dict.fromkeys(protected)
        if before.count(phrase) != after.count(phrase)
    ]
    differences = bool(numbers["changed"] or urls["changed"] or phrases
                       or unicode_changes["changed"] or code["changed"])
    diff = list(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="original", tofile="candidate",
    ))
    return {
        "status": "requires_review" if differences else "no_heuristic_differences",
        "numbers": numbers, "urls": urls, "protected_phrase_changes": phrases,
        "unicode_changes": unicode_changes, "code_changes": code,
        "candidate_inspection": inspect_text(after),
        "diff": diff[:MAX_DIFF_LINES],
        "omitted_diff_lines": max(0, len(diff) - MAX_DIFF_LINES),
        "semantic_equivalence": "not_verified",
        "watermark_status": "not_verified",
    }


def main(argv=None):
    if sys.version_info < (3, 10):
        print(json.dumps({"status": "input_error", "error": "Python 3.10+ required"}),
              file=sys.stderr)
        return 2
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
            report["status"] = "inspection_only"
            report["watermark_status"] = "not_verified"
        else:
            if any(not phrase for phrase in args.protect):
                raise ValueError("protected phrases must not be empty")
            after, candidate_hash = read_text(args.candidate)
            report = compare_text(before, after, args.protect)
            report["candidate_sha256"] = candidate_hash
        report["original_sha256"] = original_hash
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "input_error", "error": str(exc)}, ensure_ascii=True),
              file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return int(report.get("status") == "requires_review")


if __name__ == "__main__":
    sys.exit(main())
