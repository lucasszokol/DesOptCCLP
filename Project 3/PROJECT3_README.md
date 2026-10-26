# Project 3: Diagnosing PINN Convergence for Cylinder Flow

This project reproduces and diagnoses convergence failure in a vanilla physics-informed neural network (PINN) for steady incompressible flow around a fixed cylinder. It then changes only the loss-weighting rule to test whether component-wise gradient balancing improves convergence.

The prototype is a controlled research experiment, not a production CFD replacement. The fixed cylinder isolates one precursor to Professor Leixin Ma's more difficult fluid–structure interaction problems.

## Experimental comparison

All models use the same five-layer, 64-neuron `tanh` architecture, collocation points, seeds, optimizer schedule, and training budget.

- `vanilla`: equal weights for continuity, two momentum residuals, inlet, walls/cylinder, and outlet.
- `balanced`: weights those six terms from their parameter-gradient norms using bounded exponential smoothing.
- `supervised`: fits the same network directly to lattice-Boltzmann fields to test whether the architecture can represent the solution.

The difficulty knob is Reynolds number: 10, 20, and 40. The primary target is to reproduce worsening vanilla-PINN convergence, not to assume the proposed remedy will succeed.

## Setup

Use Python 3.11 or 3.12. Install the stable CUDA-enabled PyTorch 2.7 build for the computer, then install the remaining dependencies. The complete CPU smoke test was verified with Python 3.12 and PyTorch 2.7. The CUDA 12.8 production environment must still pass the verification command below on this machine:

```powershell
py -3.11 -m venv .venv-project3
.\.venv-project3\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-project3.txt
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0)); x=torch.tensor([2.0],device='cuda',requires_grad=True); y=x**3; g=torch.autograd.grad(y,x,create_graph=True)[0]; print(torch.autograd.grad(g,x)[0])"
```

## Commands

Generate the conventional reference fields:

```powershell
python project3.py reference
```

Train all methods for three seeds and three Reynolds numbers:

```powershell
python project3.py train
```

Generate P1–P5 figures, the summary table, and the predefined decision result:

```powershell
python project3.py analyze
```

Run the complete workflow:

```powershell
python project3.py all
```

Use `--quick` for a pipeline smoke test. Quick-mode numbers are not scientific results:

```powershell
python project3.py all --quick --output project3_results_quick
```

Run verification checks:

```powershell
python -m unittest tests.test_project3_pinn -v
```

## Outputs

- `project3_results/reference/`: lattice-Boltzmann fields and convergence metadata.
- `project3_results/runs/`: checkpoints, histories, evaluation fields, and metrics.
- `project3_results/figures/`: required P1–P5 diagnostic figures.
- `project3_results/analysis/summary.csv`: all run metrics.
- `project3_results/analysis/decision.json`: the predeclared 25% improvement decision.

Training data from the conventional solver are used only by the supervised capacity control. The vanilla and balanced PINNs use the equations and boundary conditions without reference-field labels.
