# Report audit fixes

- Corrected the published description of the three topology starts and the
  different SLSQP and trust-constr variable scalings; removed the topology
  bonus claim for the all-fin result.
- Added an independent SciPy boundary-value cross-check of the production
  nonlinear fin residual and tangent at 8 and 16 elements. The submitted human
  benchmark truth remains untouched. This additional BVP result is a numerical
  reference, not an independently derived exact solution. The check records
  maximum nodal errors, tangent finite-difference errors, and Newton residual
  ratios; final-results validation rejects a missing or failed check.
- Added the Q4 mesh-convergence log--log figure from the canonical JSON and
  clarified the actual finite-difference timing bug in the AI-use statement.
- The base field shader evaluates the four-node bilinear Q4 interpolation per
  fragment instead of linearly interpolating vertex colors across triangles.
- Corrected image sizing that otherwise caused page-wide phone overflow.

## Verification

- Human-gate check: passed; human benchmark and approval files not changed.
- Full `run_all` completed. After adding the Newton-ratio check and final
  payload validation, the supplementary fin evidence was regenerated with
  that final implementation and the payload revalidated and site rebuilt;
  GitHub CI must exercise the final single command from a clean checkout.
- `pytest Project4/tests -q`: 38 passed. `node --check` and `git diff --check`
  passed; reproduced engineering results matched the prior integration data.
- Independent BVP maximum nodal error: approximately 0.004503 K at 8 elements
  and 0.001125 K at 16. Worst tangent directional relative error: 2.62e-9.
- Isolated Chrome preview at 1280 x 900 and 390 x 844: final results loaded,
  no browser errors, two metric panels, MathJax available, hover/click and
  phone tap inspection worked, and playback changed the rendered frame. Both
  layouts had document width within viewport; long display equations remain
  horizontally scrollable inside their containers. Browser checks used the
  local preview; public post-deployment review is still necessary.
