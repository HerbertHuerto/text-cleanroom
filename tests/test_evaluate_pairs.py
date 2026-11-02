import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts"))
import evaluate_pairs


class PairEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        before, after = b"Synthetic original", b"Synthetic candidate"
        (self.root / "original.txt").write_bytes(before)
        (self.root / "candidate.txt").write_bytes(after)
        self.manifest = {"schema_version": 1, "detector": {
            "name": "test-fixture-not-a-detector", "version": "1", "scope": "reference_known_key",
            "configuration_id": "test-only", "threshold": 3.0, "positive_when": "at_least", "minimum_tokens": 200},
            "pairs": [{"id": "sample", "original": "original.txt", "candidate": "candidate.txt",
                       "original_sha256": hashlib.sha256(before).hexdigest(),
                       "candidate_sha256": hashlib.sha256(after).hexdigest(),
                       "original_score": 4.0, "candidate_score": 2.0,
                       "original_tokens": 400, "candidate_tokens": 400}]}

    def evaluate(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest))
        return evaluate_pairs.evaluate(path)

    def test_transition_is_not_a_production_claim(self):
        report = self.evaluate()
        self.assertEqual(report["observed_transition_fraction"], 1)
        self.assertEqual(report["production_textgrain_removal"], "not_established")
        self.assertEqual(report["score_authenticity"], "not_independently_verified")

    def test_negative_baseline_and_short_text_excluded_from_denominator(self):
        pair = self.manifest["pairs"][0]
        for field, value, expected in [
            ("original_score", 1, "baseline_not_detected_not_removal_evidence"),
            ("candidate_tokens", 100, "excluded_below_detector_minimum"),
        ]:
            with self.subTest(field=field):
                self.manifest["pairs"] = [{**pair, field: value}]
                report = self.evaluate()
                self.assertEqual(report["observations"][0]["outcome"], expected)
                self.assertIsNone(report["observed_transition_fraction"])

    def test_remains_detected_and_at_most_direction(self):
        self.manifest["pairs"][0]["candidate_score"] = 5
        self.assertEqual(self.evaluate()["observed_transition_fraction"], 0)
        self.manifest["detector"].update(threshold=0.01, positive_when="at_most")
        self.manifest["pairs"][0].update(original_score=0.001, candidate_score=0.2)
        self.assertEqual(self.evaluate()["observed_transition_fraction"], 1)

    def test_changed_text_cannot_reuse_scores(self):
        (self.root / "candidate.txt").write_text("different bytes")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_invalid_scores_counts_and_duplicate_pairs_fail(self):
        original = copy.deepcopy(self.manifest)
        for field, value in [("original_score", float("nan")), ("candidate_score", float("inf")),
                             ("candidate_score", True), ("candidate_tokens", True), ("candidate_tokens", -1)]:
            self.manifest = copy.deepcopy(original)
            self.manifest["pairs"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.evaluate()
        self.manifest = original
        self.manifest["pairs"].append(copy.deepcopy(original["pairs"][0]))
        with self.assertRaises(ValueError):
            self.evaluate()


if __name__ == "__main__":
    unittest.main()
