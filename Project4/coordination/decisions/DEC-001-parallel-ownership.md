# DEC-001 — Parallel ownership and merge policy

Status: accepted

Five independent agents use GitHub as asynchronous shared state. Each receives
exclusive file ownership and creates one branch and one pull request. No agent
works directly on `main`; no implementation agent merges another lane. Agent 5
audits cross-lane contracts and prepares integration, while Lucas or another
explicitly authorized maintainer controls merges and academic submissions.

This avoids concurrent edits to a shared dump file, preserves reviewable Git
history, and prevents one agent from treating another agent's unmerged claims
as authoritative evidence.
