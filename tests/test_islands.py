from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts"))
from islands import freeze, protected_spans, restore, restore_result


class IslandTests(unittest.TestCase):
    def test_nested_overlapping_and_repeated_fragments(self):
        original = "banana Ada Ada"
        self.assertEqual(protected_spans(original, ["ana", "nan", "Ada"]), [(1, 6), (7, 10), (11, 14)])
        parts = freeze(original, ["ana", "nan", "Ada"])
        candidate = " ".join(p["placeholder"] for p in reversed(parts))
        self.assertEqual(restore(candidate, parts, True), "Ada Ada anana")

    def test_exact_unicode_newlines_code_and_replacement_metacharacters(self):
        fragment = 'می‌روم 👩‍💻\r\n```sh\nrm -rf /tmp/build\n```\n$1 \\1'
        islands = freeze(fragment, [fragment])
        self.assertEqual(restore(islands[0]["placeholder"], islands, True).encode(), fragment.encode())

    def test_missing_duplicate_unknown_and_malformed_markers_fail(self):
        islands = freeze("Ada", ["Ada"])
        marker = islands[0]["placeholder"]
        for text in ["Ada", marker * 2, marker + "[[TCI:000000000000:0]]", marker + "[[TCI:broken]]"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                restore(text, islands, True)

    def test_collision_rejected(self):
        with self.assertRaises(ValueError):
            freeze("literal [[TCI:someone]]", [])

    def test_locators_restored_but_are_not_semantic_validation(self):
        islands = freeze("Ada pays 20.", ["Ada"])
        candidate = islands[0]["placeholder"] + " pays 200."
        output, mapping = restore_result(candidate, [{"fact_id": "F1", "candidate_quote": candidate}], islands)
        self.assertEqual(mapping[0]["candidate_quote"], output)
        self.assertIn("200", output)  # Integrity/semantic review must still reject it.

    def test_no_immutable_regions(self):
        self.assertEqual(restore("ordinary prose", [], True), "ordinary prose")


if __name__ == "__main__":
    unittest.main()
