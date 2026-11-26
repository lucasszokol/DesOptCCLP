# Rubric presentation fixes

- Build readable verification, gradient/cost, KKT, nonlinear comparison, and uncertainty evidence directly from the canonical results JSON into the static page. Viewer JavaScript replaces the same panels when it loads.
- Add verification tolerances and explicit linear/nonlinear mass and fin-height comparisons to the interactive page; clarify engineering assumptions and distinguish an infeasible specification from an implementation bug.
- Add the Project 4 team to the repository README. No numerical results, human benchmark answers, or approvals changed.
- Focused static-site test passed; Node syntax and git whitespace checks passed. Full test suite is running and CI must verify the final commit.
- Local isolated Chrome checks passed at desktop and 390-pixel phone width: final data, two metrics panels, hover/click/tap, animation, no browser errors or broken images, no MathJax errors. Wide equations scroll within their containers on phones.
- The temperature limits remain illustrative assumptions rather than sourced component ratings; topology bonus is not claimed. Public deployment and Canvas submission remain separate checks.
