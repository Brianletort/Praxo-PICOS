# Task Packet

## Identity
- project_key: praxo-picos
- linear_issue_id:
- linear_session_id:
- run_id:
- risk_tier: 0|1|2|3

## Goal
<one paragraph statement>

## Acceptance criteria
- [ ] ...
- [ ] ...

## Scope boundaries
In scope:
- ...
Out of scope:
- ...

## Constraints
- Security constraints:
- Testing required:
- Data quality required:
- Performance required:

## Required evaluations
- unit_tests: required|optional
- security_scan: required|optional
- data_quality: required|optional
- performance: required|optional

## Gates
- required_gates: [architecture, data, security, performance, release, merge]

## Tool allowances
Allowed:
- repo read/write
- run tests locally
Requires approval:
- schema changes
- infra/deploy changes
- prod actions / data mutation

## Output contract
Deliver:
1) PR link
2) Summary of changes
3) How tested (exact commands + results)
4) DQ/perf results (if required)
5) Risks + rollback notes
