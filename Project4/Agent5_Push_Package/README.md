# Agent 5 push package

This folder contains the complete `agent/integration-audit-20261117` work.
The simplest method is to push the branch from the existing repository:

```bash
cd "/Users/charliegreen/Desktop/Design Optimization/DesOptCCLP"
git switch agent/integration-audit-20261117
git push --set-upstream origin agent/integration-audit-20261117
```

After the push, open:

<https://github.com/lucasszokol/DesOptCCLP/compare/main...agent/integration-audit-20261117>

## Package contents

- `agent-integration-audit-20261117.bundle`: a self-contained Git bundle with
  the branch and all three commits.
- `patches/`: three ordered `git format-patch` files. Apply them to current
  `main` with `git am` if the existing local branch is unavailable.
- `files/`: complete copies of every changed file, preserving repository paths.
- `changed-files.txt`: the exact changed-path inventory.
- `SHA256SUMS`: integrity hashes for the package files.

## Restore from the bundle

```bash
git clone agent-integration-audit-20261117.bundle DesOptCCLP-Agent5
cd DesOptCCLP-Agent5
git remote set-url origin https://github.com/lucasszokol/DesOptCCLP.git
git push --set-upstream origin agent/integration-audit-20261117
```

The branch is based on `origin/main` commit `f61dfd0`. Its tip is
`fbe1249733ee468eabe022743dea0d95ed48ae7f`.
