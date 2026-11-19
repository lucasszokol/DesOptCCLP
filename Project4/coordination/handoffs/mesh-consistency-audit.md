# Mesh-consistency correction handoff

The November 19 audit found that the former midpoint-edge load applied the
20 mm chip power over 21 mm, and the unnormalized KS sum changed with the
number of chip nodes. The proposed DEC-003 corrects the footprint, samples
15 fixed physical positions including the chip edges, and adds a 0.5 K
numerical reserve while leaving the approved physical limits unchanged.

The global FE matrix and tangent now use sparse assembly and sparse linear
solves. The joint height/density mass Hessian and scaled-coordinate mapping
are corrected. The actual piecewise-linear chip peak is independently checked.

The complete reproduction completed successfully: 20/20 benchmark checks,
72/72 sensitivity sweeps, the nonlinear fin cross-check, and 24/24 final
design/uncertainty mesh reanalyses. The maximum KS change between the 320×32
and 400×40 meshes is about 0.0242 K, below the documented 0.1 K criterion.
The nominal optimized mass is about 0.177304 kg and the uncertainty optimized
mass is about 0.181634 kg. The mesh study is not a proof of the infinite-mesh
limit; point-like fin roots remain a modeling limitation.

The full test suite passed 41 tests; exact footprint integration, sparse
tangents, mesh-invariant KS on the same field, and mixed Hessian derivatives
have regression coverage. The local isolated browser preview showed both
metric panels, working WebGL, hover/tap, animation, MathJax, and no browser
errors at 1280 px and 390 px; document width stayed within the viewport.

DEC-003 remains pending team review. Existing benchmark truth and approval
files are unchanged. The public report is not updated by this branch until
the team accepts the amendment and the final deployment succeeds.
