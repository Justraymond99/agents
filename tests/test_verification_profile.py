import copy
import unittest
from atlas.verification_profile import validate_profile


EXAMPLE = {
    "version": 1,
    "project": "Example app",
    "description": "Illustrative only",
    "prerequisites": ["Use a disposable local checkout"],
    "checks": [
        {"id": "unit", "phase": "verify", "argv": ["python", "-m", "unittest"],
         "expected": "Exit 0 with passing tests", "risk": "local tests", "approval_required": False}
    ],
}


class ProfileTests(unittest.TestCase):
    def test_valid_profile(self):
        self.assertEqual(validate_profile(EXAMPLE), [])

    def test_reject_non_object(self):
        self.assertTrue(validate_profile([]))

    def test_reject_unknown_version(self):
        case = copy.deepcopy(EXAMPLE)
        case["version"] = 2
        self.assertTrue(validate_profile(case))

    def test_reject_shell_command_string(self):
        case = copy.deepcopy(EXAMPLE)
        case["checks"][0]["argv"] = "rm -rf /"
        self.assertTrue(validate_profile(case))

    def test_reject_missing_evidence(self):
        case = copy.deepcopy(EXAMPLE)
        case["checks"][0]["expected"] = ""
        self.assertTrue(validate_profile(case))

    def test_reject_duplicate_check_id(self):
        case = copy.deepcopy(EXAMPLE)
        case["checks"].append(copy.deepcopy(case["checks"][0]))
        self.assertTrue(validate_profile(case))

    def test_require_verify_phase(self):
        case = copy.deepcopy(EXAMPLE)
        case["checks"][0]["phase"] = "setup"
        self.assertTrue(validate_profile(case))

    def test_require_explicit_approval_flag(self):
        case = copy.deepcopy(EXAMPLE)
        del case["checks"][0]["approval_required"]
        self.assertTrue(validate_profile(case))


if __name__ == "__main__":
    unittest.main()
