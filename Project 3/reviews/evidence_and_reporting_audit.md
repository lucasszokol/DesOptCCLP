# Project 3 — Independent evidence, statistics, and reporting audit

**Reviewer:** Christian / Teammate 4

**Review date:** October 27, 2026 (America/Phoenix)

**Reviewed main:** `fb18d065c771ca27ccacada55ae5417aba46b86c`

**Status:** Retrospective evidence audit; not a preregistration or independent reproduction of production training.

## 1. Finding, scope, and evidence provenance

**The committed summary records a negative performance result for this balancing implementation:** at Re=40, median relative velocity error rises from 0.22384254 to 0.72767383, a reduction of **−225.0829%** (error increases by 225.0829%, to 3.250829 times vanilla). The existing combined no-slip metric and divergence also worsen. This arithmetic is independently reproducible from the committed CSV. It does not establish a unique optimization mechanism or independently validated CFD accuracy.

**Independent physical reference adequacy remains unresolved, although external plausibility evidence has improved.** The code's adequacy flags pass its stopping, endpoint-volume-balance, and grid-disagreement checks. The new DFG 2D-1 comparison places the Re=20 drag and pressure difference within 7.25% of official values, but the outlet and cylinder discretizations differ. Do not equate `references_adequate: true` with all scientific validation concerns being resolved.

Sources inspected, relative to `Project 3/`:

- `TEAMMATE_PROMPTS.md`, `PROJECT3_README.md`, `Project_3_Report.md`, `Project_3_Literature_Review.md`, `Leixin_Ma_Recommendation_Memo.md`, and `Leixin_Ma_Feedback_Email.md`.
- `project3_pinn/{config,geometry,lbm,pinn,analysis,cli}.py`, `tests/test_project3_pinn.py`, and `build_project3_notebook.py`.
- `project3_results/experiment_config.json`, `analysis/summary.csv`, `analysis/decision.json`, `analysis/lbm_grid_refinement.json`, `analysis/lbm_external_validation.json`, saved reference JSON/NPZ files, all production histories/metric JSONs, and the two representative Re=40, seed-0 evaluation-field archives used by P4.
- `Project_3_Report.ipynb` structure: Markdown report cells plus one command cell, with no executed outputs. This is a report copy, not execution evidence.
- [Teammate 1's open reference-validation PR #3](https://github.com/lucasszokol/DesOptCCLP/pull/3), reviewed as an unmerged teammate finding. Its audited main is `713111f54fe2d821ca19892394a7b7a276676bf2`, not this review's snapshot. The intervening `lbm.py` changes concern refinement selection and reporting; core solver/stopping logic is unchanged. Do not transplant the older 8-versus-16-node refinement conclusion onto the newer 16-versus-24-node comparison.

The CSV contains 27 unique `(Re, method, seed)` entries: Re=10/20/40, vanilla/balanced/supervised, seeds 0/1/2. The current project includes every run's history, evaluation JSON, and training JSON, plus the two representative field archives needed to regenerate P4. Large checkpoints and the other 25 field archives remain excluded, so exact retraining state and arbitrary new field plots are not preserved. No production training or CFD sweep was launched during this audit. Interview claims remain team-attributed; no consent record or original transcript was independently verified.

The supplied October 26 draft was a useful proposed protocol. This revision replaces its outdated “all results pending” status, preserves useful proposed checks, and separates them from implemented measurements. New criteria proposed here are retrospective suggestions or future-run protocol; they were not frozen before these outcomes were inspected.

## 2. Requirements-to-evidence checklist

Statuses mean **verified artifact/code fact**, **reported but not independently reproduced**, or **unresolved**; a passing software check is not a physical-validation pass.

| Requirement | Evidence now available | Finding / remaining evidence |
|---|---|---|
| P1 steady reference | JSON histories and stopping implementation for all three Re | Four consecutive checks concern changes in **u only**. Stationarity of v, density, pressure, and drag remains unverified. |
| P1 conservation | Endpoint metric and saved velocity fields | Endpoint volume balance is imposed by the outlet. Independent local and density-weighted conservation remains unresolved. |
| P1 grid adequacy | Re40 16/24-node comparison: 1.3702575%; configured tolerance 5% | Passes the implemented disagreement criterion; not absolute fine-grid error or matched external validation. No Re20 refinement artifact was found. |
| P1 physical plausibility | Recorded drag/wake; PR #3; DFG 2D-1 comparison | Re20 drag is 7.25% high and nondimensional pressure difference is 6.29% high. This supports plausibility, but the outlet and cylinder discretizations are not exactly matched. |
| P1 costs | Reference runtime in JSON | Report machine/workload context; initialization is not fully included in the current solver timer. |
| P2 losses, norms, cosines, weights | Logging source and all 27 production histories | The revised figure shows six losses, six weighted norms, magnitude ratio, adaptive weights, and all 15 cosine histories. For Re40 seed 0, continuity/inlet is negative at 90% of vanilla and 97% of balanced logging points. Histories cover Adam, not L-BFGS. |
| P3 error and seed variation | 27 summary rows, three seeds per cell | Arithmetic and coverage can be checked; raw prediction/error regeneration is blocked by missing production artifacts. |
| P3 capacity control | Same architecture in source; low supervised velocity error | Supports ability to fit reference velocity with labels. Does not prove physical boundary accuracy or isolate optimization from every other loss/sampling issue. |
| P4 spatial/wake analysis | Figure-generation source, representative seed-0 fields, and regenerated figure | Re40 vanilla/balanced maps now share one scale. The lower plot is a common streamwise error-power spectrum after row detrending and Hann windowing over the stated wake region. It remains a spatial diagnostic, not proof of spectral bias. |
| P5 training/inference/memory | Summary timings, timer source | No separate optimizer-phase timings or peak-memory fields; inference is a synchronized single pass, not a warmed repeated benchmark. |
| Decision integrity | CSV, decision JSON, analysis source | Error threshold fails. Decision code does not enforce paired seed completeness, no-slip, or comprehensive integrity checks. |
| Reproducibility | Source, configuration, tests, reference artifacts, run histories/metrics, representative P4 fields | P1–P5 regenerate from saved results. Large checkpoints, initial failures/restarts, and nonrepresentative field archives are not retained. |

### Reference diagnostics and threshold provenance

Using each saved production field, define `Q(x)=dy*nansum_y(u)` and `max_x |Q(x)-Q(0)|/|Q(0)|`. Independently recomputed maximum departures are **1.0456%, 0.7927%, and 0.6655%** for Re=10/20/40. These are section-volume-flux diagnostics with the saved masks and rectangular quadrature, not exact population-link mass budgets or absolute flow-error estimates. The Re10 value agrees with PR #3's reported diagnostic.

Saved production coordinates have `dx=0.0625` and `dy≈0.06212121`, a roughly 0.606% mismatch. PR #3 discusses coordinate mapping and effective boundary placement; this discrepancy remains present. The recorded 1.37% Re40 refinement difference does not by itself eliminate shared modeling/mapping errors.

The 5% grid threshold is present in current configuration and metadata. Git history introduces that configuration field in the same commit as the completed-results study; this inspection does **not** establish that it was agreed before results were viewed. Likewise, preserve the team's stated 25% criterion but use “team-declared,” not “preregistered,” unless a dated prior record is supplied. The separate cylinder/wall guardrail below is a new recommendation.

## 3. Metric definitions: implemented versus proposed

Use nondimensional mean inlet velocity `U=1`, cylinder diameter `D=1`, and identical evaluation sets for paired methods. Compute each metric **per run first**, then summarize seeds; do not pool grid points across seeds as independent replicates. Missing/nonfinite data must be explicitly flagged, never silently dropped or replaced with values chosen to improve an outcome.

| Metric | Current implementation and interpretation | Recommended supplement / correction |
|---|---|---|
| Relative velocity error | `E=||[u_hat-u_ref,v_hat-v_ref]||_2/(||[u_ref,v_ref]||_2+1e-12)` on `~solid`, uniformly weighted, against the **production 16-node** reference | For nonuniform quadrature use `sqrt(sum A_k*|error_k|² / sum A_k*|reference_k|²)`. A 24-node reevaluation is a separately labeled sensitivity analysis, not the existing CSV metric. |
| Spatial error | `sqrt((u_hat-u_ref)²+(v_hat-v_ref)²)`; solids masked | Divide by U if dimensional; common color scale and mask, with prespecified seed 0. Avoid pointwise division by near-zero reference velocity. |
| Pressure error | Subtract fluid-domain mean of `p_hat-p_ref`; report `||aligned_error||_2/(||p_ref||_2+1e-12)` | Keep this convention when reproducing CSV. Also report aligned RMS with explicit pressure scale. Outlet-mean alignment is an alternative metric, not what the CSV uses. Gauge alignment is evaluation postprocessing, not model training. |
| Divergence | `sqrt(mean((u_x+v_y)²))`, autograd, up to 4,096 fluid-grid samples selected using `seed+991` | Same samples within each seed pair; sampling differs across seeds. Normalize by U/D if dimensional. Supplement with maps/regions; finite-difference reference diagnostics are not directly identical to neural autograd metrics. |
| Existing no-slip | `wall_velocity_rms=sqrt(mean over points AND components of [u_hat²,v_hat²]))`, fixed sample seed 17; equal numbers on bottom, top, cylinder | This is component RMS, not vector-magnitude RMS, and not boundary-length weighting. At identical points, vector RMS is sqrt(2) times this value. Existing aggregate cannot recover separate surface errors. |
| Proposed separate no-slip | Not currently stored | For each cylinder/wall boundary, `S_Gamma=sqrt(sum a_j*(u_hat²+v_hat²)/sum a_j)/U`, with arc/length quadrature. Report cylinder and flat walls separately, plus 95th percentile or maximum speed. Define endpoint/corner treatment. |
| Endpoint volume imbalance | `abs(sum u_out-sum u_in)/(abs(sum u_in)+1e-12)`; exported as `mass_imbalance` | Name it **volume-flux imbalance** for this diagnostic. Record raw/corrected outlet flux separately where available. Density-weighted flux and time-dependent storage/link budgets are different checks; inspect wall leakage too. |
| Drag | Continuum neural traction on 720 circular samples: `C_D=2*integral[-p*n_x+(2*u_x*n_x+(u_y+v_x)*n_y)/Re] ds`; normal points outward from body into fluid | Dimensional definition is `F_x/(0.5*rho*U²*D)` per unit span. LBM momentum-exchange drag has a different discretization; verify normalization and boundary resolution before comparing. Report unresolved traction accuracy explicitly. |
| Recirculation | Neural field: last negative-u sample on 2,000 centerline points from rear+0.001 to x=12, minus rear x; zero if none. LBM uses a discrete near-center row | Prefer contiguous near-wake interval and interpolated reattachment; mark truncated or unresolved intervals. Report zero as “none resolved,” not proof of no recirculation. Current last-negative rule can include disconnected downstream pockets. |
| Gradient magnitudes | All trainable parameters; `g_i=grad_theta L_i`, `G_i=||g_i||_2`; weighted magnitudes `w_i*G_i`. Summary takes temporal median of largest/smallest positive finite norms | State excluded zero/nonfinite norms and denominator policy. Report six named terms, not only a ratio. |
| Gradient alignment | `C_ij=(g_i dot g_j)/(G_i*G_j)` for 15 pairs when norm product exceeds `1e-20`; otherwise pair omitted. Summary minimum is over logged checks | Undefined is not zero. Require complete valid-pair accounting. A minimum near −0.995 proves at least one strong local opposition, **not persistent conflict** or causation. Inspect time histories and valid negative-pair fraction. |
| Weights | Configured bounds 0.1–10, mean-one projection, EMA 0.9; logged at diagnostic steps | Verify each update in available histories to declared numerical tolerance; log saturation duration. Current histories cover Adam; they do not establish final L-BFGS behavior. |
| Numerical failure | Source writes exception records; finite summary entries exist | Report failed/scheduled by method/Re and seed, separately from incomplete and finite-but-inaccurate runs. Initial failures/restarts need an immutable manifest; absence of current failure files is insufficient because successful completion removes a failure record. |
| Wall time | Reference JSON runtime, per-run training seconds, synchronized batched full-grid inference seconds and query count | Report phase/setup/data-generation costs separately. Do not call existing timers complete end-to-end costs. Use warm-up and repeated inference trials, median and spread; distinguish CPU/GPU and transfer costs. |
| Memory | Not reported in committed summary | Measure training and inference peak CPU RSS and GPU allocated/reserved memory separately; state device, precision, batch/query size, reset/measurement method. Mark unavailable until measured. |

For auxiliary inlet error, use RMS vector mismatch to the parabolic profile; for outlet error, separately report RMS streamwise derivatives and pressure variation versus the selected gauge condition. These are proposed supplementary measurements, not summary columns.

For a reusable surrogate and a defined repeated-case workload, `N*=(T_data+T_train)/(T_reference-T_inference)` only if the denominator is positive. Include data generation, validation, and retraining where applicable. A separate PINN trained per case has no demonstrated cross-case reuse; do not infer design-sweep savings from pointwise inference on an already solved case.

## 4. Three-seed statistics and decision rules

At each Re/method report all three seeds, median, minimum, and maximum. The observed range is **not a confidence interval**. No claim of statistical significance or broad robustness is supported by this descriptive three-seed design. Also show paired reductions `I_s=100*(1-E_bal,s/E_van,s)`; these do not replace the primary ratio-of-medians endpoint:

`I40 = 100*(1 - median_s(E_bal,40,s)/median_s(E_van,40,s))`.

If vanilla median is zero, the ratio is undefined. Require unique, matched seeds and finite metrics before applying the rule. Preserve failed and incomplete scheduled runs; do not select favorable replacements.

Re40 medians independently recalculated from the committed CSV:

| Metric | Vanilla | Balanced | Supervised |
|---|---:|---:|---:|
| Relative velocity L2 | 0.22384254 | 0.72767383 | 0.00561775 |
| Existing combined component-RMS slip | 0.01149344 | 0.03405492 | 0.07099015 |
| Sampled divergence RMS | 0.04121187 | 0.10449163 | 0.06028343 |

The supervised control demonstrates low reference-velocity error, but its boundary/divergence metrics prevent describing it as uniformly more physically accurate. Interpret capacity support narrowly: this architecture can fit the velocity labels, while training objective, sampling, conditioning, and optimization may all contribute to the PINN gap.

Use three separate verdicts:

1. **Recorded performance:** the 25% velocity improvement target fails; existing aggregate no-slip also worsens. This is a negative result relative to the stored reference and metrics.
2. **Physical validity:** conditional/unresolved until independent reference and provenance concerns are addressed. Do not upgrade a numerical comparison into validated CFD truth.
3. **Mechanism:** inconclusive as a unique causal diagnosis. Lower weighted gradient ratios plus worse errors argue that magnitude equalization alone was insufficient; they do not uniquely establish direction conflict or weight saturation as the cause.

For future experiments, recommend success require both separate median cylinder and wall slip to be no greater than vanilla, with any absolute tolerance justified **before** examining results. Report per-seed degradation even if medians pass. Applying that new definition to these runs is a retrospective sensitivity check and requires fresh boundary evaluations. It cannot make the already failed velocity target pass.

“Failure reproduced” should mean poor reference-field accuracy under the specified architecture and finite optimizer budget, with trajectories and supervised comparison disclosed. It is not a theorem that training cannot converge or that no PINN can solve the PDE. The machine decision currently lacks explicit seed-count/pairing/no-slip checks; its Boolean is not the complete verdict above.

## 5. Figure and table specifications

These are reporting requirements and proposed additions, not assertions that every current figure implements them. Every caption must give source artifact, commit, Re, seed selection, mask, units, and production/quick status.

| Item | Specification / caption guidance |
|---|---|
| P1 | Reference field; u stopping history with threshold/four-check rule; local/section flux; grid comparison and runtime table. Caption: “Implemented stopping and resolution diagnostics; endpoint volume balance is imposed and does not establish independent conservation.” |
| P2 | Six unweighted losses, weighted objective separately; six norms and weights; weighted ratios; 15 named pairwise cosines with undefined handling. Include both methods and disclose Adam-only history. Caption: “Local gradient interactions; magnitude balance does not establish field accuracy.” |
| P3 | All three seed markers for each Re/method, median and observed min–max; per-seed table. Caption: “Error against the production LBM reference; ranges show three seeds, not confidence intervals.” |
| P4 | Shared color scale/mask for vanilla/balanced seed 0; wake-centerline velocity and error; explicitly spatial spectrum with sampling, windowing, detrending, and normalization |
| P5 | Reference solve, training, and full-grid inference, with hardware and point count; separate missing phase/memory measurements |
| Decision table | Re/method/seed, velocity error, paired change, current combined slip, proposed separate slip if measured, failure/completion/provenance status |

Current P4 code computes the magnitude of a **2D FFT of error speed**, replacing masked NaNs by zero and averaging magnitudes across transverse frequency bins. This is not a windowed centerline power spectrum or temporal spectrum. Separate autoscaling can mislead visual comparisons. Proposed line spectra/common scales require analysis-owner coordination; do not caption existing figures as if these changes already exist.

Current P2/P4 use seed 0. Call it a fixed representative example, not the median or best run. P3 currently plots medians/ranges without individual seed markers. P1 selects the maximum configured Re; supplement a per-Re table rather than imply all references are displayed.

## 6. Proposed report passages and outcome templates

**Suggested current-results replacement:**

> In the committed three-seed summary at Re=40, adaptive balancing increases median relative velocity error from 0.22384 to 0.72767 (225.1% higher), missing the team's 25% reduction target. The existing aggregate no-slip and sampled divergence metrics also worsen. This is a negative performance finding against the selected numerical reference. Independent reference-validation concerns and missing production run provenance limit physical and causal interpretation. The supervised network's low velocity error supports representational capacity for this label-fitting task, but does not establish superior boundary satisfaction. Gradient-direction conflict and weight saturation remain hypotheses for targeted follow-up, not uniquely established causes.

**Positive template, for a future adequately validated comparison:**

> Across three paired seeds, median velocity error changed from [V] to [B], a reduction of [I]%, meeting the 25% target; the previously specified no-slip guardrail [definition] also passed. Reference/provenance checks [list] support this comparison. Diagnostics [findings] support [limited mechanism claim], with [remaining uncertainty]. No FSI or cross-case speedup is inferred.

**Negative template:**

> With [reference and provenance qualifications], this implementation achieved [I]% reduction and [boundary result], failing [specified target]. This intervention was insufficient under the tested budgets. The result does not establish categorical PINN failure or a unique causal mechanism.

**Inconclusive template:**

> A conclusion about [physical accuracy / performance / mechanism] remains unresolved because [specific missing gate]. Available artifacts establish [limited finding]. The smallest next verification is [action]. Do not erase an observable recorded error increase merely because its physical interpretation is conditional.

The recommendation memo and email draft should soften “clear optimization failure” to “poor physics-informed training performance under the tested objective and budget.” Recommendations to prioritize graph surrogates are architectural proposals informed by the interview/literature, not measured superiority in this experiment. Do not send or rewrite those artifacts as part of this review.

## 7. Unsupported claims and interview talking points

This experiment cannot demonstrate moving-boundary FSI, unsteady/turbulent accuracy, unseen-geometry or unseen-Re generalization, laboratory validation, superiority over mature commercial solvers, measured MeshODENet CFD performance, population-level robustness from three seeds, or a unique gradient-conflict cause. Scalar positive weights leave instantaneous pairwise gradient directions unchanged, but can change the optimization trajectory; “cannot rotate gradients” is not proof that weighting can never help.

- **Interview motivation:** attribute claims to the team's interview summary until original notes/speakers/permission are verified. Do not invent quotations or imply endorsement.
- **Published distinction:** Liu and Ma's [MeshODENet](https://arxiv.org/abs/2509.18445) combines GNNs and neural ODEs and demonstrates structural-mechanics applications. The primary arXiv record identifies the related [journal DOI](https://doi.org/10.1115/1.4071488). The arXiv record was checked October 27; the publisher page returned HTTP 403. This supports the structural-surrogate distinction, not cylinder-flow performance.
- **Faithful simplification:** fixed-cylinder flow retains nonlinear momentum, incompressibility, and competing boundary/equation losses, while omitting structural dynamics, mesh motion, and interface feedback.
- **Researcher-facing message:** magnitude balancing did not improve recorded field accuracy here. Test selective physical constraints and alternative optimization interventions with reference validation and full costs before extending to coupled FSI.
- **Scope discipline:** this review does not independently verify the PhD student's Mamba/FSI presentation or attribute its claims to Professor Ma.

## 8. Verification, blockers, and handoff

Review checks: fetched current main; inspected open PR #3; confirmed 27 unique summary keys and three seeds per Re/method; recalculated Re40 medians and improvement; inspected saved coordinate spacing and section-volume-flux departures; compared core solver source across the two reviewed commits. Production experiments were not rerun.

Relevant test command, from `Project 3/`:

```powershell
python -m unittest tests.test_project3_pinn -v
```

Local result: **9 passed, 2 skipped because PyTorch is unavailable**, 11 total. The initial sandbox run encountered temporary-folder permission errors; rerunning outside that sandbox completed. These are implementation tests, not independent physical validation. PR #3 reports 16 passing tests in its own CPU environment; that is the teammate's result, not this reviewer's local result.

Do not run `python project3.py analyze` against the committed production directory without restoring run artifacts: analysis collects per-run evaluation files, not the existing summary, and writes decision/figure outputs. Use an isolated output copy for future regeneration. Do not start another production sweep just to fill reporting gaps.

| Priority | Owner | Smallest next action |
|---|---|---|
| Critical | Reference reviewer / solver owner | Reconcile PR #3 with current main; resolve local/density-weighted conservation, stationarity and coordinate/boundary concerns; document which gates are implementation versus physical validation. |
| Critical | Training owner | Supply a manifest plus per-run evaluation/training JSON and histories for all 27 rows, with code/config hashes, seed identities, failures/restarts, and artifact locations. Large checkpoints need not be duplicated in Git. |
| High | Analysis owner | Preserve existing metrics; label proposed alternatives; verify paired coverage/no-slip explicitly and separate performance, validity, and mechanism decisions. |
| High | Analysis owner | Regenerate common-scale maps and complete gradient diagnostics from restored artifacts in an isolated directory; do not infer persistence from a single minimum cosine. |
| High | Team | Locate dated records for thresholds; label any newly adopted criteria retrospective or prospective. |
| Medium | Compute owner | Measure missing phase timings, warmed repeated inference, and training/inference memory under a declared workload. |
| Medium | Report owner | Verify interview attribution/permission; adopt qualified passages in report/memo/email after team review. |

**Handoff:** This file supplies all seven Teammate 4 deliverables: checklist, metric/aggregation definitions, figure/table specifications, three-seed statistics, outcome templates, unsupported claims, and interview talking points. It proposes coordinated corrections without modifying solver code, teammates' reviews, the main report, or production outputs.
