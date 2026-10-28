# MeshODENet-Style Surrogate versus PINN for Flow Around a Fixed Cylinder

## 1. A proposed flow-specific architecture

A model similar to MeshODENet [1] could represent the fluid domain as a fixed graph: **nodes** would be fluid mesh points, **edges** would encode neighboring connections and relative positions, and node features would include coordinates, velocity $(u,v)$, Reynolds number, and inlet/wall/cylinder/outlet indicators. A graph neural network would estimate the **velocity time derivative**, and fixed-step **RK4** would advance the velocity field using four network evaluations per step.

For incompressible flow, this adaptation would also require pressure coupling (for example, a pressure-Poisson projection), prescribed inlet and no-slip velocities, a compatible outlet treatment, and checks of divergence and mass conservation. RK4 step-size sensitivity and long-rollout stability would need verification. Training would require **time-resolved CFD trajectories**; reuse across Reynolds numbers or geometries would depend on held-out validation. The published MeshODENet study concerns deformable structures, **not** cylinder-flow CFD [1].

**Illustrative architecture assumptions:** $|V|=22{,}745$ nodes, $|E|\approx4|V|=90{,}980$ directed edges, $L=5$ message-passing layers, latent width $d=64$, and $S=100$ RK4 steps. These are cost-model inputs, not measurements of a fluid MeshODENet.

## 2. A fair experiment

The comparison would use **one PINN trained per flow condition** versus **one MeshODENet-style surrogate trained across several conditions**, with the same cylinder geometry, boundary conditions, CFD reference, evaluation grid, hardware, and error measures. An illustrative held-out test would train the surrogate with $Re=10$ and $40$ trajectories and assess it at $Re=20$; two training conditions alone would not establish reliable generalization.

Both methods should be compared at **matched velocity accuracy**, reporting relative velocity $L_2$ error, divergence, no-slip error, runtime, and peak memory. The surrogate's cost must include CFD trajectory generation. Its ability to handle changed cylinder geometries would require separate training and testing with varied meshes. A supervised feed-forward network is not a MeshODENet benchmark.

## 3. PINN and MeshODENet complexity derivations with assumptions stated

Let $Q$ be PINN evaluation points, $H$ its hidden-layer count, $w$ its width, $B$ collocation points per update, $K$ optimization steps, $c_{AD}$ the overhead of automatic differentiation, and $P$ model parameters. For the graph model, $N_D$ denotes training trajectories, $K_G$ training epochs, $S$ RK4 steps, $L$ graph layers, $d$ latent width, and $C_{proj}$ the cost of **one** pressure projection. Assume dense width-$d$ message/update networks, a fixed graph, and one projection per RK4 stage.

| Operation | Case-specific PINN | MeshODENet-style fluid adaptation |
|:--|:--|:--|
| **Inference work** | $O(QHw^2)$ | $O\big(4S[L(|V|+|E|)d^2+C_{proj}]\big)$ |
| **Training work** | $O(Kc_{AD}BHw^2)$ | $O\big(K_GN_D4S[L(|V|+|E|)d^2+C_{proj}]\big)$, plus CFD generation |
| **Inference memory** | $O(QHw+P)$ without query batching | $O(L(|V|+|E|)d+P)$ plus projection buffers |
| **Training activation memory** | At least $O(BHw)$; greater for PDE derivatives | Up to $O(SL(|V|+|E|)d)$ with stored rollouts |

For the PINN comparison, $H=5$, $w=64$, and $B=4{,}096$; the graph dimensions above are assumed. Backpropagation, checkpointing, graph sparsity, and pressure-solver choice affect actual costs. Asymptotic complexity **does not establish wall-clock speed**.

## 4. Total-cost equations including reference-data generation

For $N$ **distinct** flow conditions, let $T_P$ denote PINN training per condition, $t_P$ PINN inference, $T_G$ surrogate training, $t_G$ complete surrogate rollout (including pressure handling), and $T_{CFD,j}$ the cost of generating each of $N_D$ CFD trajectories.

$$
T_{\mathrm{PINN}}(N)=N(T_P+t_P)
$$

$$
T_{\mathrm{MeshODE}}(N)=\sum_{j=1}^{N_D}T_{CFD,j}+T_G+Nt_G
$$

These totals exclude shared validation, storage, and hardware costs. Repeated predictions of **one already-trained PINN for the same condition** instead cost approximately $Nt_P$; they do not require repeated PINN training.

## 5. A crossover calculation for repeated flow cases

For $Re=40$, the team's **measured three-seed median vanilla-PINN** values are $T_P=478.355\,\mathrm{s}$, $t_P=0.003133\,\mathrm{s}$ for 22,745 evaluation points, and relative velocity $L_2$ error $0.223843$.

For a **hypothetical MeshODENet-style benchmark**, assume $N_D=20$ CFD trajectories at $375\,\mathrm{s}$ each, surrogate training $T_G=10{,}000\,\mathrm{s}$, and complete RK4 inference $t_G=30\,\mathrm{s}$ per condition. The surrogate's training and reference-data generation would therefore total $17{,}500\,\mathrm{s}$. **None of these graph-model timings has been measured or published for cylinder flow.**

$$
N_* = \frac{N_DT_{CFD}+T_G}{T_P+t_P-t_G}
=\frac{20(375)+10{,}000}{478.355+0.003133-30}
\approx39.03.
$$

Thus, **40 distinct new flow conditions** is the first integer crossover in this *assumed* cost scenario, provided the surrogate reaches at least the PINN's measured accuracy and satisfies physical constraints. The real crossover is unknown, and generalization to 40 new cases has not been demonstrated. For repeat queries of the **same** already-trained condition, the PINN is cheaper per query under these assumptions.

## 6. A report-ready comparison table with verified primary citations

| Criterion | Case-specific PINN | MeshODENet-style fluid adaptation |
|:--|:--|:--|
| Learned output | Steady $(u,v,p)$ | RK4-integrated velocity with additional pressure handling [1] |
| Training information | PDE residuals and boundary conditions | Time-resolved CFD trajectories and mesh connectivity [1] (fluid adaptation) |
| Reuse across conditions | New PINN training per condition in this comparison | Potential reuse only after multi-condition training and validation |
| $Re=40$ relative velocity $L_2$ | **0.223843**, measured median | **$\leq0.223843$** comparison target; actual error unknown |
| Training and CFD-data cost | **478.355 s**, measured median training | **10,000 s** assumed training + **7,500 s** assumed CFD generation |
| Evaluation cost | **0.003133 s**, measured median | **30 s** assumed full rollout |
| Conservation / memory | PDE and boundary losses; MLP | Additional pressure/conservation treatment; graph and rollout memory |
| Published evidence | Measured cylinder-flow comparison | MeshODENet validated on structural systems, **not** this fluid problem [1] |

**Primary citation:** [1] K. Liu and L. Ma, *MeshODENet: A Graph-Informed Neural Ordinary Differential Equation Neural Network for Simulating Mesh-Based Physical Systems* (2025 preprint), [arXiv:2509.18445](https://arxiv.org/abs/2509.18445). The experimental context follows the [Design Optimization Project 3 instructions](https://designinformaticslab.github.io/DesignOptimization2025/project3.html). PINN values are from the team's cylinder-flow measurements; all MeshODENet timings are explicitly **hypothetical**.

## 7. Claims the present experiment cannot support

- That MeshODENet has been implemented, validated, or shown to outperform a PINN for fixed-cylinder flow.
- That the illustrative surrogate runtimes, memory, accuracy, or **40-case crossover** represent measured CFD performance.
- That message passing or RK4 automatically ensures incompressibility, conservation, or steady-state convergence.
- That training on a small Reynolds-number set ensures generalization to other conditions or cylinder geometries.
- That a supervised feed-forward model establishes MeshODENet accuracy or total cost.
