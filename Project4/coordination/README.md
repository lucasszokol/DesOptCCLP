# Five-Agent GitHub Coordination

This directory is the shared asynchronous memory for five independent agents.
The agents do not share conversation state. They coordinate through merged
repository files, GitHub Issues, branch commits, pull-request discussion, CI,
and per-agent handoffs.

## Start condition

The five Goal Mode prompts may be launched after the human gate is complete:

1. A team member approves `SPECIFICATION.md` in `approvals.yaml`.
2. Students independently complete `HUMAN_BENCHMARK_WORKSHEET.md` and commit
   the transcribed `tests/benchmark_truth.yaml` with attestation.

Until then, agents may inspect or review but must not run the graded campaign or
manufacture expected answers.

## Parallel lanes

Each lane has exclusive write ownership defined in `TASKS.md`. Agents may read
all files, but an agent that discovers a defect outside its lane must document
it in its issue and handoff rather than editing the other lane's files.

Every agent must:

1. Pull `origin/main` and confirm the human gate.
2. Create or update the GitHub Issue named in its task.
3. Create its exact branch from the latest `main`.
4. Work only in its owned paths.
5. Run focused and full verification.
6. Write a unique handoff using `HANDOFF_TEMPLATE.md`.
7. Push the branch and open a pull request using the repository template.

Agent 5 is the integration/audit lane. It may review Agents 1–4 immediately,
but it must not silently copy unmerged changes. Lucas or an explicitly
authorized maintainer controls merges to `main`.

## Conflict prevention

- One branch and one PR per lane.
- One owner per file path.
- One unique handoff file per agent; never append to a shared log.
- Decisions affecting multiple lanes go in a new file under `decisions/` and
  require a GitHub Issue comment from Agent 5 before implementation.
- If upstream changes make a lane's assumptions invalid, stop, update the
  issue, and request integration direction.

## Sources

The structure follows official OpenAI guidance that `AGENTS.md` supplies
durable repository instructions, while Goals remain thread-scoped completion
contracts rather than shared memory:

- <https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex>
- <https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex>
