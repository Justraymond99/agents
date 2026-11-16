import unittest
from atlas.verification_report import Check, validate_report


class VerificationReportTests(unittest.TestCase):
    def test_evidenced_pass_is_consistent(self):
        self.assertEqual(validate_report((Check("pytest", "passed", "exit 0; 12 passed"),), "verified"), [])

    def test_unsupported_pass_is_rejected(self):
        self.assertTrue(validate_report((Check("pytest", "passed"),), "verified"))

    def test_failed_check_cannot_be_called_verified(self):
        self.assertTrue(validate_report((Check("pytest", "failed", "exit 1"),), "verified"))

    def test_blocked_requires_reason(self):
        self.assertTrue(validate_report((Check("e2e", "blocked"),), "blocked"))
        self.assertEqual(validate_report((Check("e2e", "blocked", reason="No browser available"),), "blocked"), [])

    def test_not_run_requires_reason(self):
        self.assertTrue(validate_report((Check("integration", "not_run"),), "partially verified"))

    def test_no_checks_cannot_be_verified(self):
        self.assertTrue(validate_report((), "verified"))

    def test_failed_verdict_requires_failure(self):
        self.assertTrue(validate_report((Check("lint", "passed", "exit 0"),), "failed"))

    def test_not_applicable_with_reason_is_allowed(self):
        self.assertEqual(validate_report((Check("migration", "not_applicable", reason="No schema change"),), "partially verified"), [])


if __name__ == "__main__":
    unittest.main()
