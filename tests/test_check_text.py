import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts/check_text.py"
spec = importlib.util.spec_from_file_location("check_text", SCRIPT)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class TextChecks(unittest.TestCase):
    def test_legitimate_unicode_and_attribution_are_not_mutated(self):
        text = "Written by Jane Doe — Claude Monet. می\u200cروم 👩\u200d💻 e\u0301\u00a0fin."
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / "original.md"
            original.write_bytes(text.encode("utf-8"))
            original.chmod(0o600)
            mode = stat.S_IMODE(original.stat().st_mode)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "inspect", str(original)],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(original.read_bytes(), text.encode("utf-8"))
            self.assertEqual(stat.S_IMODE(original.stat().st_mode), mode)
            self.assertEqual(list(Path(folder).iterdir()), [original])
            report = json.loads(result.stdout)
            self.assertEqual(report["occurrences"], 3)
            self.assertEqual(report["watermark_status"], "not_verified")

    def test_changed_facts_are_reported(self):
        report = checks.compare_text(
            "Jane Doe paid €20.50 twice: €20.50. https://example.org/a",
            "John Doe paid €20.50. https://example.org/b", ["Jane Doe"],
        )
        self.assertEqual(report["status"], "requires_review")
        self.assertTrue(report["numbers"]["changed"])
        self.assertTrue(report["urls"]["changed"])
        self.assertEqual(report["protected_phrase_changes"][0]["after"], 0)

    def test_equal_token_counts_do_not_claim_semantic_equivalence(self):
        report = checks.compare_text("A costs 10, B costs 20", "A costs 20, B costs 10", [])
        self.assertEqual(report["status"], "no_heuristic_differences")
        self.assertEqual(report["semantic_equivalence"], "not_verified")
        self.assertTrue(report["diff"])

    def test_sign_changes_and_uppercase_url_schemes_are_reported(self):
        for before, after in [
            ("Balance -10", "Balance 10"),
            ("Balance −10", "Balance +10"),
            ("Balance -.5", "Balance .5"),
            ("Balance −,5", "Balance +,5"),
            ("Fraction .5", "Integer 5"),
            ("Value 1e-3", "Value 1e3"),
            ("HTTPS://example.org/a", "HTTPS://other.example/a"),
        ]:
            with self.subTest(before=before):
                self.assertEqual(checks.compare_text(before, after, [])["status"], "requires_review")

    def test_attribution_and_code_can_be_protected_explicitly(self):
        for phrase in ["Written by Jane Doe", "Made by local artisans", "`print(42)`"]:
            with self.subTest(phrase=phrase):
                self.assertEqual(checks.compare_text(phrase, "", [phrase])["status"], "requires_review")

    def test_reports_truncation_without_losing_failure(self):
        text = "\u200b" * 110
        self.assertEqual(checks.inspect_text(text)["omitted_occurrences"], 10)
        before = "\n".join(str(i) for i in range(250))
        report = checks.compare_text(before, "", [])
        self.assertEqual(report["status"], "requires_review")
        self.assertGreater(report["omitted_diff_lines"], 0)
        self.assertGreater(report["numbers"]["omitted_unique_tokens"], 0)

    def test_rejects_unsupported_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, data in [
                ("code.py", b"print(1)"), ("text.txt", b"\xff"),
                ("nul.md", b"a\x00b"), ("huge.txt", b"x" * (checks.MAX_BYTES + 1)),
            ]:
                with self.subTest(name=name):
                    path = Path(folder) / name
                    path.write_bytes(data)
                    with self.assertRaises((ValueError, UnicodeError)):
                        checks.read_text(path)

    @unittest.skipUnless(os.name == "posix", "FIFO check requires POSIX")
    def test_fifo_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pipe.txt"
            os.mkfifo(path)
            with self.assertRaises(ValueError):
                checks.read_text(path)

    def test_cli_exit_codes_and_newline_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            original, candidate = [Path(folder) / name for name in ("a.md", "b.md")]
            original.write_bytes(b"Price 20\r\n")
            candidate.write_bytes(b"Price 30\n")
            base = [sys.executable, str(SCRIPT), "compare", str(original), str(candidate)]
            changed = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(changed.returncode, 1)
            self.assertEqual(original.read_bytes(), b"Price 20\r\n")
            candidate.write_bytes(original.read_bytes())
            same = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(same.returncode, 0)
            error = subprocess.run(base + ["--protect", ""], capture_output=True, text=True)
            self.assertEqual(error.returncode, 2)


if __name__ == "__main__":
    unittest.main()
