#!/usr/bin/env python3
"""Summarize supplied paired detector observations; this is not a detector."""

import argparse
import json
import math
from pathlib import Path
import sys

from check_text import read_text
from route_policy import load_json, require_keys


def number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("scores and thresholds must be finite numbers")
    return value


def evaluate(path):
    manifest, manifest_hash = load_json(path)
    require_keys(manifest, {"schema_version", "detector", "pairs"})
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported evaluation schema")
    detector = manifest["detector"]
    require_keys(detector, {"name", "version", "scope", "configuration_id", "threshold",
                            "positive_when", "minimum_tokens"})
    for field in ("name", "version", "configuration_id"):
        if not isinstance(detector[field], str) or not detector[field].strip():
            raise ValueError("detector identity and configuration are required")
    if detector["scope"] not in {"reference_known_key", "production_authorized"}:
        raise ValueError("unknown detector scope; generic AI classifiers are not watermark detectors")
    if detector["positive_when"] not in {"at_least", "at_most"}:
        raise ValueError("threshold direction is required")
    threshold = number(detector["threshold"])
    minimum = detector["minimum_tokens"]
    if type(minimum) is not int or minimum < 1:
        raise ValueError("minimum_tokens must be a positive integer")
    pairs = manifest["pairs"]
    if not isinstance(pairs, list) or not pairs or len(pairs) > 1000:
        raise ValueError("evaluation requires 1 to 1000 paired observations")
    rows, seen = [], set()
    for pair in pairs:
        require_keys(pair, {"id", "original", "candidate", "original_sha256", "candidate_sha256",
                            "original_score", "candidate_score", "original_tokens", "candidate_tokens"})
        if not isinstance(pair["id"], str) or not pair["id"] or pair["id"] in seen:
            raise ValueError("pair IDs must be nonempty and unique")
        seen.add(pair["id"])
        scores = {}
        for side in ("original", "candidate"):
            if not isinstance(pair[side], str):
                raise ValueError("text file paths are required")
            _, actual_hash = read_text(Path(path).resolve().parent / pair[side])
            if pair[side + "_sha256"] != actual_hash:
                raise ValueError("detector observation is bound to different text bytes")
            count = pair[side + "_tokens"]
            if type(count) is not int or count < 1:
                raise ValueError("detector-tokenizer counts must be positive integers")
            score = number(pair[side + "_score"])
            scores[side] = score >= threshold if detector["positive_when"] == "at_least" else score <= threshold
        if min(pair["original_tokens"], pair["candidate_tokens"]) < minimum:
            outcome = "excluded_below_detector_minimum"
        elif not scores["original"]:
            outcome = "baseline_not_detected_not_removal_evidence"
        elif scores["candidate"]:
            outcome = "signal_still_detected"
        else:
            outcome = "detected_to_not_detected"
        rows.append({"id": pair["id"], "outcome": outcome,
                     "original_score": pair["original_score"], "candidate_score": pair["candidate_score"]})
    eligible = sum(row["outcome"] in {"signal_still_detected", "detected_to_not_detected"} for row in rows)
    changed = sum(row["outcome"] == "detected_to_not_detected" for row in rows)
    return {"status": "supplied_observations_summarized", "manifest_sha256": manifest_hash,
            "detector": detector, "observations": rows, "eligible_baseline_detected_pairs": eligible,
            "detected_to_not_detected_pairs": changed,
            "observed_transition_fraction": changed / eligible if eligible else None,
            "score_authenticity": "not_independently_verified",
            "interpretation": "Only this supplied detector/configuration; not proof of universal absence.",
            "production_textgrain_removal": "not_established"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.manifest)
    except Exception as exc:
        print(json.dumps({"status": "evaluation_failed", "error_type": type(exc).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
