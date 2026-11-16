"""Fixture tests of the correction hierarchy, not an LLM quality benchmark."""
import unittest

from atlas.correction_tree import CorrectionCase, select_layer


class CorrectionTreeTests(unittest.TestCase):
    def test_redesign_precedes_other_layers(self):
        case = CorrectionCase("unsafe overwrite", redesign=True, lint=True, verify=True, rule=True)
        self.assertEqual(select_layer(case), "redesign")

    def test_lint_precedes_verification_and_prose(self):
        case = CorrectionCase("invalid skill metadata", lint=True, verify=True, rule=True)
        self.assertEqual(select_layer(case), "lint")

    def test_verify_when_no_deterministic_static_check(self):
        case = CorrectionCase("visual layout regression", verify=True, rule=True)
        self.assertEqual(select_layer(case), "verify")

    def test_rule_only_when_executable_checks_cannot_cover_judgment(self):
        case = CorrectionCase("explain architectural tradeoff", rule=True)
        self.assertEqual(select_layer(case), "rule")

    def test_human_review_fallback(self):
        case = CorrectionCase("ambiguous high-risk tradeoff")
        self.assertEqual(select_layer(case), "human-review")

    def test_mandatory_human_approval_is_orthogonal(self):
        case = CorrectionCase("production credential rotation", redesign=True, human_approval_required=True)
        self.assertEqual(select_layer(case), "redesign")
        self.assertTrue(case.human_approval_required)


if __name__ == "__main__":
    unittest.main()
