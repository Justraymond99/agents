#!/usr/bin/env python3
"""Static ATLAS Core installation check; not an IDE runtime test."""
import argparse
from pathlib import Path

SKILLS = ("investigate-bug", "implement-feature", "review-code")


def _valid_skill_metadata(content: str, expected: str) -> bool:
    lines = content.splitlines()
    if len(lines) < 4 or lines[0].strip() != "---":
        return False
    try:
        end = lines.index("---", 1)
    except ValueError:
        return False
    metadata = {}
    for line in lines[1:end]:
        if ":" not in line:
            return False
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key or key in metadata:
            return False
        metadata[key] = value.strip("\"'")
    return metadata.get("name") == expected and bool(metadata.get("description", "").strip())


def check(project: Path, client: str):
    if client not in ("codex", "claude", "cursor"):
        raise ValueError(f"Unsupported client: {client}")
    required = [Path("AGENTS.md")]
    required.extend(Path("atlas/skills") / s / "SKILL.md" for s in SKILLS)
    if client == "codex":
        required.extend(Path(".agents/skills") / s / "SKILL.md" for s in SKILLS)
    elif client == "claude":
        required.append(Path("CLAUDE.md"))
    else:
        required.append(Path(".cursor/rules/atlas.mdc"))
    errors = []
    for rel in required:
        path = project / rel
        if not path.is_file():
            errors.append(f"MISSING {rel}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"EMPTY {rel}")
    if client == "codex":
        for skill in SKILLS:
            rel = Path(".agents/skills") / skill / "SKILL.md"
            path = project / rel
            if path.is_file() and not _valid_skill_metadata(path.read_text(encoding="utf-8"), skill):
                errors.append(f"INVALID SKILL METADATA {rel}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--client", choices=("codex", "claude", "cursor"), required=True)
    args = parser.parse_args()
    errors = check(args.project.expanduser().resolve(), args.client)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS: ATLAS Core files are present and structurally valid.")
    print("This does not prove IDE discovery or instruction compliance.")
    print('Manual test: ask your assistant "Which ATLAS skills are available? Do not edit anything."')


if __name__ == "__main__":
    main()
