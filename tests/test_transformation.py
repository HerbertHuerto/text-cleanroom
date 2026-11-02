from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts"))
from transformation import compare_wording, longest_match, segments


class TransformationTests(unittest.TestCase):
    def test_cosmetic_changes_are_not_reconstruction(self):
        report = compare_wording("One two three four five six seven eight.", "ONE, two; three four five six seven eight!")
        self.assertTrue(report["unchanged_editable_word_sequence"])
        self.assertEqual(report["shared_windows"]["8"]["original_retained_fraction"], 1)
        self.assertEqual(report["longest_copied_editable_run"]["words"], 8)
        self.assertEqual(report["watermark_status"], "not_verified")

    def test_protected_quotes_are_not_rewrite_targets_or_crossed(self):
        text = "one two QUOTE three four"
        report = compare_wording(text, text, ["QUOTE"])
        self.assertEqual(report["longest_copied_editable_run"]["words"], 2)
        self.assertEqual(report["shared_windows"]["3"]["original_unique"], 0)
        self.assertEqual(report["protected_characters"]["original"], 5)

    def test_nested_protection_is_not_double_counted(self):
        report = compare_wording("Claude Monet paints.", "Claude Monet paints.", ["Claude", "Claude Monet"])
        self.assertEqual(report["protected_characters"]["original"], len("Claude Monet"))

    def test_empty_or_all_protected_is_not_perfect_removal(self):
        report = compare_wording("Ada", "Ada", ["Ada"])
        self.assertIsNone(report["shared_windows"]["5"]["original_retained_fraction"])
        self.assertIsNone(report["editable_word_count_ratio"])
        self.assertEqual(report["longest_copied_editable_run"]["words"], 0)

    def test_insertion_padding_does_not_hide_original_retention(self):
        original = "one two three four five six seven eight"
        report = compare_wording(original, "lots of brand new irrelevant material " + original)
        self.assertEqual(report["shared_windows"]["5"]["original_retained_fraction"], 1)
        self.assertGreater(report["editable_word_count_ratio"], 1)

    def test_removed_protected_fragment_still_visible_as_counts_not_approval(self):
        report = compare_wording("Ada says hello", "says hello", ["Ada"])
        self.assertEqual(report["protected_characters"], {"original": 3, "candidate": 0})
        self.assertEqual(report["status"], "wording_diagnostics_only")

    def test_changed_negation_can_change_wording_without_preserving_meaning(self):
        report = compare_wording("not all funding has been paid", "no funding has been paid")
        self.assertFalse(report["unchanged_editable_word_sequence"])
        self.assertEqual(report["semantic_equivalence"], "not_verified")

    def test_unicode_and_character_offsets(self):
        original = "α β γ δ epsilon zeta eta theta"
        candidate = "new α β γ δ epsilon zeta eta theta end"
        run = compare_wording(original, candidate)["longest_copied_editable_run"]
        self.assertEqual(run["words"], 8)
        self.assertEqual(candidate[slice(*run["candidate_range"])], original[slice(*run["original_range"])])

    def test_suffix_match_against_brute_force_on_repeated_random_sequences(self):
        rng = random.Random(73)
        for _ in range(150):
            left = [rng.choice("abc") for _ in range(rng.randrange(1, 40))]
            right = [rng.choice("abc") for _ in range(rng.randrange(1, 40))]
            expected = 0
            for i in range(len(left)):
                for j in range(len(right)):
                    width = 0
                    while i + width < len(left) and j + width < len(right) and left[i + width] == right[j + width]:
                        width += 1
                    expected = max(expected, width)
            a, _ = segments(" ".join(left), [])
            b, _ = segments(" ".join(right), [])
            result = longest_match(a, b)
            self.assertEqual(result["words"], expected)

    def test_large_repetitive_input_and_bounds(self):
        text = "word " * 10000
        self.assertEqual(compare_wording(text, text)["longest_copied_editable_run"]["words"], 10000)
        with self.assertRaises(ValueError):
            compare_wording("word " * 20001, "word")

    def test_many_protected_words_fail_before_automaton_allocation(self):
        # A 1 MiB input used to create 500,000 empty chunks and unique states.
        from unittest import mock
        import transformation
        text = "a " * 500000
        with mock.patch.object(transformation, "longest_match") as matcher:
            with self.assertRaisesRegex(ValueError, "10,000 protected matches"):
                compare_wording(text, text, ["a"])
            matcher.assert_not_called()

    def test_protected_only_segments_are_not_allocated(self):
        chunks, protected = segments("a " * 10000, ["a"])
        self.assertEqual(chunks, [])
        self.assertEqual(protected, 10000)


if __name__ == "__main__":
    unittest.main()
