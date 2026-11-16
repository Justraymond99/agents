#!/usr/bin/env python3
"""Non-destructive installation of ATLAS Core into an existing project."""
import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = ("codex", "claude", "cursor")


def _copy_exclusive(src: Path, dest: Path) -> bool:
    """Create only a new file; never follow or replace an existing destination."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(dest, flags, 0o666)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "wb") as target, src.open("rb") as source:
            shutil.copyfileobj(source, target)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    return True


def install(project: Path, client: str, dry_run: bool = False):
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    if client not in CLIENTS:
        raise ValueError(f"Unsupported client: {client}")
    project = project.resolve()
    skills = sorted((ROOT / "atlas" / "skills").glob("*/SKILL.md"))
    files = [(ROOT / "AGENTS.md", project / "AGENTS.md")]
    files.extend((p, project / p.relative_to(ROOT)) for p in skills)
    if client == "codex":
        files.extend((p, project / ".agents" / "skills" / p.parent.name / "SKILL.md") for p in skills)
    elif client == "claude":
        files.append((ROOT / "CLAUDE.md", project / "CLAUDE.md"))
    else:
        files.append((ROOT / "config" / "atlas.mdc", project / ".cursor" / "rules" / "atlas.mdc"))

    # Fail before changing the destination if the distribution is incomplete.
    missing = [str(src.relative_to(ROOT)) for src, _ in files if not src.is_file()]
    if missing:
        raise ValueError("Missing ATLAS source templates: " + ", ".join(missing))

    created, skipped = [], []
    for src, dest in files:
        rel = str(dest.relative_to(project))
        # Reject symlinked parent directories, including dangling links.
        parents = list(reversed(dest.relative_to(project).parents))
        current = project
        unsafe = False
        for part in dest.relative_to(project).parts[:-1]:
            current = current / part
            if current.is_symlink():
                unsafe = True
                break
        if unsafe:
            skipped.append(rel)
            continue
        if dest.exists() or dest.is_symlink():
            skipped.append(rel)
            continue
        if dry_run:
            created.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Recheck parent components after creation; never intentionally traverse links.
        current = project
        for part in dest.relative_to(project).parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ValueError(f"Unsafe symlinked destination parent: {current}")
        if _copy_exclusive(src, dest):
            created.append(rel)
        else:
            skipped.append(rel)
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
