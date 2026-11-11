# Human Gate Checklist

The parallel Goal prompts are ready only when every box is checked by a person.

- [x] The team reviewed `Project4/SPECIFICATION.md`.
- [x] `Project4/approvals.yaml` exists with `specification_approved: true`.
- [x] The approver names and date are present.
- [x] Students independently completed `HUMAN_BENCHMARK_WORKSHEET.md`.
- [x] `Project4/tests/benchmark_truth.yaml` contains the transcribed answers.
- [x] The truth file has `status: student_verified` and an attestation.
- [x] The two human-authored files are committed and pushed to `main`.
- [x] Each teammate has repository write access and a distinct assigned lane
  documented in `ASSIGNMENTS.md` and the corresponding GitHub issue.
- [ ] Lucas sends exactly one Goal prompt from `GOAL_PROMPTS.md` to each agent.

The gate does not certify that the answers are correct. Agent 1 verifies them
against the independent solver after the gate; disagreement must be reported,
not silently replaced.
