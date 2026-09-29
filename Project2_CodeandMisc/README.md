# Ill-Conditioned Aircraft Spar Truss

This repository contains Team Optimus Prime's Project 2 report and reproducible finite element analysis. The report is the submission for this assignment, but this document goes through the steps for replicating results or using the software for a different analysis. 

- Read [`Project_2_Report.md`](Project_2_Report.md) for the submission report. 
- Edit [`truss_config.py`](truss_config.py) to enter node coordinates, member connections, supports, and loads.
- Follow [`ANSYS_Verification.md`](ANSYS_Verification.md) to reproduce the $r=10{,}000$ displacement solution in ANSYS MAPDL.
- Run `project2_truss.py` to regenerate all numerical results and figures.
- Run `python -m unittest discover -s tests -v` to execute the verification checks.

## Setup

```bash
python -m pip install -r requirements.txt
python project2_truss.py
```

The documented example uses a 14-node Warren-style truss. The analysis assembles the stiffness matrix from the editable structural lists; a user never enters the matrix directly. It compares gradient descent with traditional conjugate gradient on the original system. Jacobi rescaling is used only for the required D2 intrinsic-conditioning diagnostic, not as an optimizer or preconditioner.

The analysis also stores the complete displacement vector in `results/u_r10000.json`, writes a node-by-node table to `results/displacements_r10000.csv`, generates `figures/deformed_truss_r10000.png`, and exports `results/ansys_model_r10000.inp` for independent verification.
