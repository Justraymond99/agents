"""Validate declarative ATLAS verification profiles. Never executes commands."""
import argparse
import json
from pathlib import Path


def validate_profile(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Profile must be a JSON object"]
    if data.get("version") != 1:
        errors.append("version must be 1")
    if not isinstance(data.get("project"), str) or not data["project"].strip():
        errors.append("project must be a nonempty string")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errors.append("description must be a nonempty string")
    if not isinstance(data.get("prerequisites"), list) or not all(
        isinstance(x, str) and x.strip() for x in data["prerequisites"]
    ):
        errors.append("prerequisites must be an array of nonempty strings")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a nonempty array")
        checks = []
    seen: set[str] = set()
    for index, check in enumerate(checks):
        label = f"checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{label} must be an object")
            continue
        name = check.get("id")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.id must be nonempty")
        elif name in seen:
            errors.append(f"{label}.id must be unique")
        else:
            seen.add(name)
        if check.get("phase") not in ("setup", "verify", "cleanup"):
            errors.append(f"{label}.phase must be setup, verify, or cleanup")
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(
            isinstance(a, str) and a.strip() for a in argv
        ):
            errors.append(f"{label}.argv must be nonempty string arguments")
        if not isinstance(check.get("expected"), str) or not check["expected"].strip():
            errors.append(f"{label}.expected must describe observable evidence")
        if not isinstance(check.get("approval_required"), bool):
            errors.append(f"{label}.approval_required must be boolean")
        if not isinstance(check.get("risk"), str) or not check["risk"].strip():
            errors.append(f"{label}.risk must be nonempty")
    if not any(isinstance(c, dict) and c.get("phase") == "verify" for c in checks):
        errors.append("at least one verify check is required")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an ATLAS profile without running commands")
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.profile.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(f"Cannot read JSON profile: {exc}")
    errors = validate_profile(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("VALID: profile structure is consistent. No commands were executed.")


if __name__ == "__main__":
    main()
