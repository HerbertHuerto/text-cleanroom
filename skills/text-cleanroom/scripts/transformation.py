#!/usr/bin/env python3
"""Read-only wording/context diagnostics. NOT a watermark or semantic detector."""

import argparse
import json
import re
import sys

from check_text import read_text
from islands import protected_spans
from route_policy import digest, load_json

WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
MAX_WORDS = 20000


def segments(text, phrases):
    spans = protected_spans(text, phrases)
    chunks, cursor, protected_chars, words = [], 0, 0, 0
    for start, end in spans + [(len(text), len(text))]:
        chunk = []
        for match in WORD.finditer(text, cursor, start):
            if words >= MAX_WORDS:
                raise ValueError("wording diagnostics support at most 20,000 editable words")
            chunk.append((match[0].casefold(), match.start(), match.end()))
            words += 1
        if chunk:
            chunks.append(chunk)
        protected_chars += end - start
        cursor = end
    return chunks, protected_chars


def windows(chunks, width):
    return {tuple(item[0] for item in chunk[i:i + width])
            for chunk in chunks for i in range(len(chunk) - width + 1)}


def longest_match(before, after):
    """Linear-size suffix automaton: avoid quadratic matching on repetitive input."""
    states = [{"length": 0, "link": -1, "next": {}, "end": -1}]
    last, original = 0, []
    for chunk in before:
        if not chunk:
            continue
        for token in chunk + [(object(), -1, -1)]:  # Never bridge protected spans.
            original.append(token)
            current = len(states)
            states.append({"length": states[last]["length"] + 1, "link": 0,
                           "next": {}, "end": len(original) - 1})
            parent = last
            while parent >= 0 and token[0] not in states[parent]["next"]:
                states[parent]["next"][token[0]] = current
                parent = states[parent]["link"]
            if parent >= 0:
                target = states[parent]["next"][token[0]]
                if states[parent]["length"] + 1 == states[target]["length"]:
                    states[current]["link"] = target
                else:
                    clone = len(states)
                    states.append({**states[target], "next": dict(states[target]["next"]),
                                   "length": states[parent]["length"] + 1})
                    while parent >= 0 and states[parent]["next"].get(token[0]) == target:
                        states[parent]["next"][token[0]] = clone
                        parent = states[parent]["link"]
                    states[target]["link"] = states[current]["link"] = clone
            last = current
    best = {"words": 0, "original_range": None, "candidate_range": None}
    for chunk in after:
        state, length = 0, 0
        for index, token in enumerate(chunk):
            while state and token[0] not in states[state]["next"]:
                state = states[state]["link"]
                length = min(length, states[state]["length"])
            if token[0] in states[state]["next"]:
                state = states[state]["next"][token[0]]
                length += 1
            else:
                length = 0
            if length > best["words"]:
                end = states[state]["end"]
                best = {"words": length,
                        "original_range": [original[end - length + 1][1], original[end][2]],
                        "candidate_range": [chunk[index - length + 1][1], token[2]]}
    return best


def compare_wording(original, candidate, protected=()):
    if any(phrase not in original for phrase in protected):
        raise ValueError("each protected phrase must occur in the original")
    before, original_protected = segments(original, protected)
    after, candidate_protected = segments(candidate, protected)
    word_counts = [sum(map(len, chunks)) for chunks in (before, after)]
    retained = {}
    for width in (3, 5, 8):
        left, right = windows(before, width), windows(after, width)
        common = len(left & right)
        retained[str(width)] = {"original_unique": len(left), "candidate_unique": len(right),
                               "shared_unique": common,
                               "original_retained_fraction": common / len(left) if left else None,
                               "candidate_copied_fraction": common / len(right) if right else None}
    longest = longest_match(before, after)
    if longest["candidate_range"]:
        start, end = longest["candidate_range"]
        longest["excerpt"] = candidate[start:end][:240]
        longest["excerpt_truncated"] = end - start > 240
    warnings = ["word_units_are_not_model_tokens", "no_validated_removal_threshold"]
    if not word_counts[0] or not word_counts[1]:
        warnings.append("no_editable_words_in_one_or_both_texts")
    if min(word_counts) < 8:
        warnings.append("too_few_words_for_some_windows")
    return {"status": "wording_diagnostics_only", "watermark_status": "not_verified",
            "semantic_equivalence": "not_verified",
            "original_sha256": digest(original.encode("utf-8")),
            "candidate_sha256": digest(candidate.encode("utf-8")),
            "normalization": "unicode_word_regex_casefold_punctuation_ignored",
            "editable_words": {"original": word_counts[0], "candidate": word_counts[1]},
            "protected_characters": {"original": original_protected, "candidate": candidate_protected},
            "protected_fraction_original": original_protected / len(original) if original else None,
            "editable_word_count_ratio": word_counts[1] / word_counts[0] if word_counts[0] else None,
            "unchanged_editable_word_sequence": [w[0] for c in before for w in c] == [w[0] for c in after for w in c],
            "shared_windows": retained, "longest_copied_editable_run": longest, "warnings": warnings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original")
    parser.add_argument("candidate")
    parser.add_argument("--ledger")
    args = parser.parse_args(argv)
    try:
        original, original_hash = read_text(args.original)
        candidate, _ = read_text(args.candidate)
        protected = []
        if args.ledger:
            ledger, _ = load_json(args.ledger)
            if ledger.get("original_sha256") != original_hash:
                raise ValueError("ledger belongs to a different original")
            protected = ledger.get("immutable")
            if not isinstance(protected, list) or len(protected) > 200:
                raise ValueError("invalid immutable list")
        report = compare_wording(original, candidate, protected)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0  # Report produced, never approval or detection.


if __name__ == "__main__":
    sys.exit(main())
