#!/usr/bin/env python3
"""Non-destructive installation of ATLAS Core into an existing project."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = ("codex", "claude", "cursor")

def install(project: Path, client: str, dry_run: bool = False):
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    if client not in CLIENTS:
        raise ValueError(f"Unsupported client: {client}")
    skills = sorted((ROOT / "atlas" / "skills").glob("*/SKILL.md"))
    files = [(ROOT / "AGENTS.md", project / "AGENTS.md")]
    files.extend((p, project / p.relative_to(ROOT)) for p in skills)
    if client == "codex":
        files.extend((p, project / ".agents" / "skills" / p.parent.name / "SKILL.md") for p in skills)
    elif client == "claude":
        files.append((ROOT / "CLAUDE.md", project / "CLAUDE.md"))
    else:
        files.append((ROOT / "config" / "atlas.mdc", project / ".cursor" / "rules" / "atlas.mdc"))
    created, skipped = [], []
    for src, dest in files:
        rel = str(dest.relative_to(project))
        if dest.exists():
            skipped.append(rel)
            continue
        created.append(rel)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    return created, skipped

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--client", choices=CLIENTS, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        created, skipped = install(args.project.expanduser().resolve(), args.client, args.dry_run)
    except ValueError as exc:
        parser.error(str(exc))
    print("DRY RUN" if args.dry_run else "ATLAS Core installed")
    for path in created:
        print(f"  + {path}")
    for path in skipped:
        print(f"  = kept existing {path} (manual merge may be required)")
    if skipped:
        print("Review skipped files and merge ATLAS instructions manually.")
    print("Next: python scripts/atlas_check.py --project PATH --client " + args.client)

if __name__ == "__main__":
    main()
