import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/text-cleanroom/scripts"))
from transformation import compare_wording


class PublicSmokeArtifacts(unittest.TestCase):
    def test_published_hashes_and_diagnostics_reproduce_offline(self):
        folder = ROOT / "examples/2026-11-02-v0.4"
        results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(len(results["cases"]), 7)
        for run in results["cases"]:
            with self.subTest(run=run["name"]):
                original = folder / run["source"]
                case = original.parent.name
                candidate = folder / (run["name"] + ".md")
                ledger_path = folder / (case + "-ledger.json")
                for kind, path in [("original", original), ("candidate", candidate), ("ledger", ledger_path)]:
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), run[kind + "_sha256"])
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                expected = json.loads((folder / (run["name"] + "-wording.json")).read_text(encoding="utf-8"))
                self.assertEqual(compare_wording(original.read_text(encoding="utf-8"), candidate.read_text(encoding="utf-8"), ledger["immutable"]), expected)
        self.assertEqual(results["production_detector_calls"], 0)
        self.assertIsNone(results["production_removal_rate"])


if __name__ == "__main__":
    unittest.main()
