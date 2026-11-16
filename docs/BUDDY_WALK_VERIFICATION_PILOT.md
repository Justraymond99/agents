# Buddy Walk verification pilot: evidence plan

Source inspected: `Buddy-Walk/buddy-walk` main branch, `README.md`, `AGENTS.md`, `package.json`, `mobile/package.json`, `team-console/package.json`, and `.github/workflows/check.yml` on 2026-11-16.

This pilot is stored in ATLAS as `examples/buddy-walk.verification.json` because the current GitHub integration does not have write permission for the Buddy Walk repository. It is **not installed** in Buddy Walk and **no commands were run**.

## Grounded checks

- Mobile `qa` script runs `npm run typecheck && npm test` from `mobile/`; the test runner is `tsx src/test/runAll.test.ts`.
- Team console's CI invokes `bunx vp check`, `bunx vp test`, and `bunx vp build` from `team-console/` only when relevant paths change. The example profile includes a build check only until the full command invocation is validated in a disposable checkout.
- The repository root `npm run lint` and `npm run build` concern a legacy web/server setup; the README calls mobile the primary deliverable. Do not substitute those for mobile verification.

## Coverage gaps

The profile cannot verify camera, GPS, haptics, screen reader behavior, Firebase sign-in, AI answers, companion sharing, or API behavior. Those require explicit test fixtures, permissions, device/emulator, test credentials, and a safe non-production backend. Do not imply passing static checks proves these features work.

## Pilot protocol

1. Have a Buddy Walk maintainer review the profile and choose a disposable test environment.
2. Install dependencies using the documented setup and inspect scripts/lockfiles.
3. Execute only approved checks and capture exact command, commit SHA, environment, exit code, and logs.
4. Reproduce a real regression, add a targeted check, and compare an ordinary coding assistant against ATLAS with independently reviewed results.
5. Propose the profile to Buddy Walk in a separate PR once permissions and team review are available.

The JSON validator checks structure, not whether commands are safe or effective.
