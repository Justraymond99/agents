#!/usr/bin/env python3
"""Static ATLAS Core installation check; not an IDE runtime test."""
import argparse
from pathlib import Path

SKILLS = ("investigate-bug", "implement-feature", "review-code")

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
            path = project / ".agents/skills" / skill / "SKILL.md"
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                if not content.startswith("---\n") or f"name: {skill}" not in content or "description:" not in content:
                    errors.append(f"INVALID SKILL METADATA {path.relative_to(project)}")
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
