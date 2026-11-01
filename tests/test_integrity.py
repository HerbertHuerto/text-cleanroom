import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts/check_text.py"
spec = importlib.util.spec_from_file_location("check_text", SCRIPT)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class IntegrityChecks(unittest.TestCase):
    def test_removed_legitimate_joiners_require_review(self):
        before = "می\u200cروم 👩\u200d💻 👨\u200d👩\u200d👧"
        after = before.replace("\u200c", "").replace("\u200d", "")
        result = checks.compare_text(before, after, [])
        self.assertEqual(result["status"], "requires_review")
        self.assertEqual(result["unicode_changes"]["missing"], {"U+200C": 1, "U+200D": 3})
        self.assertFalse(checks.compare_text(before, before, [])["unicode_changes"]["changed"])

    def test_variation_selectors_and_blank_characters_are_visible(self):
        chars = "".join(chr(0xE0100 + i) for i in range(12))
        chars += "\ufe00\ufe0f\u2009\u3164\u2800\u034f\u115f\u1160\uffa0\u2061"
        result = checks.inspect_text("Hello" + chars)
        self.assertEqual(result["occurrences"], len(chars))
        self.assertEqual(len(result["characters_for_contextual_review"]), len(chars))
        changed = checks.compare_text("Hello", "Hello" + chars, [])
        self.assertEqual(changed["status"], "requires_review")
        self.assertEqual(sum(changed["unicode_changes"]["added"].values()), len(chars))
        self.assertEqual(changed["watermark_status"], "not_verified")

    def test_every_non_ascii_space_is_inspected_without_deletion(self):
        spaces = "\u00a0\u1680" + "".join(chr(i) for i in range(0x2000, 0x200B))
        spaces += "\u202f\u205f\u3000"
        self.assertEqual(checks.inspect_text(spaces)["occurrences"], len(spaces))
        self.assertEqual(checks.inspect_text("normal space\t\r\n")["occurrences"], 0)

    def test_unicode_limits_do_not_hide_late_changes(self):
        before = "\u200b" * 200 + "\ufe0f"
        report = checks.compare_text(before, before[:-1], [])
        self.assertEqual(report["status"], "requires_review")
        self.assertEqual(report["unicode_changes"]["missing"], {"U+FE0F": 1})
        self.assertGreater(report["candidate_inspection"]["omitted_occurrences"], 0)

    def test_positions_use_same_line_separators_as_diff(self):
        for separator in ["\n", "\r\n", "\r", "\u2028", "\u2029", "\x85", "\v", "\f"]:
            with self.subTest(separator=repr(separator)):
                report = checks.inspect_text("first" + separator + "next\u200b")
                item = report["characters_for_contextual_review"][-1]
                self.assertEqual((item["line"], item["column"]), (2, 5))

    def test_fenced_and_inline_code_changes_are_reported_without_protect(self):
        for before, after in [
            ("```sh\nrm -rf /tmp/build\n```", "```sh\nrm -rf /\n```"),
            ("Use `--dry-run`", "Use `--force`"),
            ("~~~sh\nold-command\n~~~\n", "~~~sh\nnew-command\n~~~\n"),
            ("``a `quoted` flag``", "``a `changed` flag``"),
            ("```text\nunclosed", "```text\nchanged"),
            ("`one\nline`", "`other\nline`"),
            ("`same` and `same`", "`same`"),
            ("   ```sh\nold\n   ````\n", "   ```sh\nnew\n   ````\n"),
        ]:
            with self.subTest(before=before):
                report = checks.compare_text(before, after, [])
                self.assertEqual(report["status"], "requires_review")
                self.assertTrue(report["code_changes"]["changed"])

    def test_fence_length_and_type_do_not_close_early(self):
        block = "````text\n```\n~~~\nprotected\n````\n"
        report = checks.compare_text(block, block.replace("protected", "changed"), [])
        self.assertEqual(report["code_changes"]["missing"], {block: 1})

    def test_unchanged_code_survives_prose_rewrite(self):
        block = "```python\nprint('hello')\n```\n"
        before = "Use `--dry-run` to preview.\n" + block
        after = "Preview safely with `--dry-run`.\n" + block
        self.assertFalse(checks.compare_text(before, after, [])["code_changes"]["changed"])
        # Escaped opening delimiters are prose; an escape inside a span is literal.
        self.assertFalse(checks.code_counts(r"escaped \`text\`"))
        self.assertEqual(checks.code_counts(r"`end\`"), {r"`end\`": 1})

    def test_equal_counts_remain_an_explicit_limit(self):
        report = checks.compare_text("A `first`, B `second`", "A `second`, B `first`", [])
        self.assertEqual(report["status"], "no_heuristic_differences")
        self.assertEqual(report["semantic_equivalence"], "not_verified")

    def test_cli_unicode_change_is_exit_one_with_structured_status(self):
        with tempfile.TemporaryDirectory() as folder:
            before, after = [Path(folder) / name for name in ("a.md", "b.md")]
            before.write_text("👩\u200d💻", encoding="utf-8")
            after.write_text("👩💻", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "compare", str(before),
                                     str(after)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "requires_review")

    def test_unsupported_runtime_is_not_a_comparison_result(self):
        with mock.patch.object(checks.sys, "version_info", (3, 9)):
            with mock.patch("sys.stderr") as stderr:
                self.assertEqual(checks.main([]), 2)
                self.assertIn("input_error", "".join(str(call) for call in stderr.write.call_args_list))


if __name__ == "__main__":
    unittest.main()
