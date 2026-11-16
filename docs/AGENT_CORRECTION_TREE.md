# Agent correction tree (ATLAS Core)

After an observed AI coding mistake, correct the earliest **reliable** layer rather than accumulating instructions:

1. **Redesign** — prevent the bad state or action by construction.
2. **Lint** — reject the pattern through deterministic static analysis, typing, tests, or CI.
3. **Verify** — demonstrate actual behavior through executable or visual checks.
4. **Rule** — use a concise skill or instruction for irreducible judgment.
5. **Human review** — escalate unresolved risk and ambiguity.

Human approval for high-impact operations is **not optional** just because an automated check passes.

## Usage

Read `atlas/skills/correct-agent-failure/SKILL.md` and ask the coding assistant:

> Use the ATLAS correct-agent-failure workflow on this regression. Gather evidence first, compare correction layers, and propose a testable change. Do not edit yet.

## Fixture evaluation

Run from repository root:

```bash
python -m unittest discover -s tests -p 'test_correction_tree.py' -v
```

The fixture tests verify only the **ordering logic** given explicitly supplied availability flags. They do not test whether an AI model chooses the right flags, follows the skill, or improves engineering quality. A real evaluation requires representative agent transcripts, independently assessed labels, and verified regression outcomes.

**Integration follow-up:** This first PR adds the portable skill and evaluation fixtures only. The Codex installer/checker currently enumerates three skills; it must be updated in a separate PR before the fourth skill is installed into target projects.
