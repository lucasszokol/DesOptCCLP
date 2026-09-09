# Project 1: Optimization Problem Formulation

**Team Optimus Prime**

---

## 1. Problem Identification and Motivation

Route optimization has become a daily necessity for many people around the world. Programs like Google or Apple Maps help people decide which route to take to work, classes, grocery stores, etc. These algorithms include many important factors such as predicted gas requirements, road closures, speed limits, and more. However, they miss one important factor which is crucial in climates like Arizona's — extreme temperatures.

While this might not be a major consideration for car users, others, largely students, who rely heavily on public transport and walking can be harmed by omitting heat exposure from the route optimization algorithm.

The Phoenix Valley experiences extreme temperatures for a significant portion of the academic year. ASU students, faculty, and campus workers who have to move between different buildings on campus can experience harmful health effects from prolonged exposure to the sun and heat, such as:

- Heat stroke
- Sunburn
- Dehydration
- Fatigue

In this project, we hope to establish an algorithm that takes both travel distance and heat exposure into consideration to provide optimal routes around the Tempe campus for minimizing health risks.

---

## 2. Decision Variables and Parameters

### Valid Route Parameter

$r_{ij} \in \{0,1\}$

Parameter specifying whether an edge starting at node $i$ and ending at node $j$ is a possible route.

- $r_{ij}=1$: the route is valid.
- $r_{ij}=0$: the route is invalid.

The set $R$ contains all valid edges.

---

### Route Selection Decision Variable

$x_{ij} \in \{0,1\} \forall(i,j)\in R$

Binary decision variable specifying whether the route uses the edge starting at node $i$ and ending at node $j$.
Only routes that are possible (those in $R$) are selectable.

- $x_{ij}=1$: edge $(i,j)$ is selected.
- $x_{ij}=0$: edge $(i,j)$ is not selected.

---

### Distance

$d_{ij}>0$

Parameter specifying the distance traveled along edge $(i,j)$ in meters.

$d_{ij}$ is continuous.

---

### Edge Temperature

$T_{ij}\in\{70,90,110\}$

Parameter specifying the temperature along edge $(i,j)$ in degrees Fahrenheit.

The three temperature regimes are:

- $70^\circ F$: Inside / air-conditioned
- $90^\circ F$: Outside / shaded
- $110^\circ F$: Outside / direct sunlight

---

### Comfort Temperature

$T_c=70^\circ F$

Parameter specifying the reference comfort temperature.

---

### Heat Exposure

$h_{ij}\geq0$

The heat exposure associated with an edge is defined as:

$$
h_{ij}=|T_{ij}-T_c|d_{ij}
$$

This represents the temperature difference from the reference comfort temperature multiplied by the distance traveled while exposed to that temperature.

---

### Weight Parameter

$$
0\leq\lambda\leq1
$$

$\lambda$ specifies the weight given to distance compared with temperature exposure.

- $\lambda=1$: purely minimize distance.
- $\lambda=0$: purely minimize heat exposure.
- $0<\lambda<1$: balance distance and heat exposure.

---

## 3. Objective Function

This is a minimization problem.

The objective function is:


$$\boxed{\min_x\sum_{(i,j)\in R}\left(\lambda d_{ij}+(1-\lambda)h_{ij}\right)x_{ij}}$$


This function minimizes the distance and temperature exposure experienced while traveling from the first node to the final node, with the selected route depending on the weight assigned by $\lambda$.

The term


$$\lambda d_{ij}+(1-\lambda)h_{ij}$$


represents the combined distance and heat cost of edge $(i,j)$.

The binary decision variable $x_{ij}$ determines whether that edge is selected and will contribute to the total cost.

If:

$$
x_{ij}=1
$$

the edge is selected and its cost is included.

If:

$$
x_{ij}=0
$$

the edge is not selected and its cost is not included.

---

## 4. Constraints

The primary constraint ensures that all selected routes are continuous:

$$
\boxed{
\sum_{j:(i,j)\in R}x_{ij}
-\sum_{j:(j,i)\in R}x_{ji}
=\begin{cases}
1, & i=s \\
-1, & i=t \\
0, & \text{otherwise}
\end{cases}
}
$$

where:

- $s$ is the starting node.
- $t$ is the destination node.
- $i$ represents the node currently being evaluated.
- $j$ represents nodes connected to node $i$.

At the starting node:

$$
\text{edges leaving}-\text{edges entering}=1
$$

so one route must leave the starting point.

At the destination:

$$
\text{edges leaving}-\text{edges entering}=-1
$$

so one route must enter the destination.

At every intermediate node:

$$
\text{edges leaving}=\text{edges entering}
$$

Therefore, if the route enters an intermediate node, it must also leave that node.

This constraint allows the solver to choose edges non-sequentially while still arriving at a continuous, sequential route from the starting point to the destination.

---

## 5. Problem Classification

This problem is specifically a Binary Integer Linear Programming (BILP) problem because the routing decision variables are binary:

$$
x_{ij}\in\{0,1\}
$$

The problem is also combinatorial, because the optimizer must select a combination of edges from the available network to form the optimal route.

The problem is nonconvex due to the binary decision variables. The feasible values of each route-selection variable are only:

$$
\{0,1\}
$$

and values between 0 and 1 are not included in the feasible set.

Despite the binary restriction, the objective function itself is still linear. It can be written in the general form:

$$
f(x)=c^Tx
$$

where $c$ represents the combined temperature and distance costs and $x$ represents the binary route-selection variables.

Therefore:

- The objective function is linear.
- The flow-conservation constraints are linear.
- The binary restriction on $x_{ij}$ makes the feasible set discrete and nonconvex.

A continuous relaxation could instead allow:

$$
0\leq x_{ij}\leq1
$$

which would make the formulation a convex linear program. However, the current formulation explicitly uses binary route-selection variables.

---

## 6. Assumptions and Simplifications

For the initial model, we make the following assumptions:

- Discrete segmented paths: Campus routes are represented as discrete edges connecting nodes.
- Constant walking speed: Walking speed is assumed to be constant anywhere on campus.
- No ongoing construction: All existing walking paths are assumed to be open and accessible.
- Three temperature regimes: Every edge is classified as either:
  - Inside / air-conditioned
  - Outside in the shade
  - Outside in direct sunlight
- Constant temperature for each regime: The temperatures are assumed to be:
  - Inside / AC: $70^\circ F$
  - Shaded: $90^\circ F$
  - Direct sun: $110^\circ F$
- Existing walking paths determine the nodes and edges: Currently existing campus paths are used to construct the routing network.

These assumptions simplify the initial optimization problem but do not perfectly represent real campus conditions.

Constant walking speed does not accurately reflect movement across campus due to changing levels of student traffic and congestion.

The constant-temperature assumption also does not perfectly represent real conditions because temperature, humidity, wind, solar exposure, and other weather conditions change throughout the day. Air-conditioning settings may also vary between buildings or even individual rooms.

---

## 7. Future Improvements

Future versions of the model could include:

- Velocity / congestion parameter: Account for student traffic and walking speeds when selecting an optimal route.
- Variable continuous temperatures: Replace the three fixed temperature regimes with real or estimated temperature data.
- Time-of-day dependence: Account for building closures, changing outdoor temperatures, and expected shade throughout the day.
- Higher-resolution routing mesh: Replace larger path segments with a finer mesh to provide more accurate thermal and routing data at different locations.
