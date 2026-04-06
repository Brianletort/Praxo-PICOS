# Praxo-PICOS Project Instructions

## Primary workflow
1. Read the linked Linear issue first.
2. Confirm acceptance criteria.
3. Inspect only the relevant files.
4. Make the smallest coherent change.
5. Add or update tests.
6. Summarize changed files, risks, and follow-up work.

## Hard constraints
- Never commit secrets.
- Never change runtime contracts without updating docs and tests.
- Every bug fix must add a regression test.
- Do not perform broad refactors unless the issue explicitly asks for them.
- Treat MemoryOS as reference only, not as the active implementation authority.

## Platform constraints
- Praxo-PICOS is a separate repo from MemoryOS.
- Default local ports are 8865, 3100, 3777, 8870, 6733, 6734.
- Local macOS validation is authoritative for packaging, permissions, and launch behavior.
- Cursor background agents run on Ubuntu — macOS-specific validation stays local.
