# AGENTS.md — Praxo-Picos Worker Rules

## Mission
Build and operate Praxo-Picos with production-grade safety, traceability, and measurable outcomes.

Project key: praxo-picos
Default risk tier: 1

## Non-negotiables
- Webhook endpoints must ACK immediately and never block on long work.
- Linear AgentSession created events must receive activity/external URL updates quickly.
- No secrets in logs, traces, prompts, PRs, or artifacts.
- Every run must have:
  - a task packet with project_key `praxo-picos`
  - trace correlation (otel_trace_id)
  - audit events for state changes and approvals
- Tier >= 2 work must be gated.

## Required outputs for any "agent-run" change
- Plan
- Test results
- DQ/perf results if required by policy
- Clear PR description with "How tested" and risk notes

## Escalate to human approval before:
- Changing webhook verification logic
- Changing RBAC/authz
- Introducing new tool execution capability
- Allowing any prod/deploy/data mutation action

## AgentOS API
Report bugs and new tasks to: https://choice-signals-wisconsin-pockets.trycloudflare.com/v1/callbacks/praxo-picos/
See `.cursor/rules/90-agentos-integration.mdc` for details.
