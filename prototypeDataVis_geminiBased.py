import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Build the ASU Subgraph Network
# ---------------------------------------------------------
G = nx.DiGraph()
T_comfort = 75.0  # Reference comfort temperature (Fahrenheit)

# Edge Data: (Node_A, Node_B, Distance_meters, Temp_Fahrenheit)
campus_edges = [
    # Route 1: Palm Walk (Direct, scorching sun)
    ("MU", "PalmWalk", 150, 110),
    ("PalmWalk", "Noble", 150, 110),

    # Route 2: Shaded Breezeway (Slight detour, moderate heat)
    ("MU", "ShadeBreezeway", 180, 88),
    ("ShadeBreezeway", "Noble", 180, 88),

    # Route 3: Air-Conditioned Building Crawl (Longest distance, cold)
    ("MU", "CoorHall_Indoor", 120, 70),
    ("CoorHall_Indoor", "EngCenter_Indoor", 220, 70),
    ("EngCenter_Indoor", "Noble", 110, 100),
]

# Populate graph & compute heat exposure h_ij = max(0, T - T_c) * d_ij
for u, v, dist, temp in campus_edges:
    h_ij = max(0.0, temp - T_comfort) * dist
    G.add_edge(u, v, distance=dist, temp=temp, heat=h_ij)

# ---------------------------------------------------------
# 2. Sweep Lambda to Trace the Pareto Front
# ---------------------------------------------------------
lambdas = np.linspace(0, 1, 100)
pareto_dict = {}

for lmbda in lambdas:
    # Set weighted edge cost: c_ij = lambda * d_ij + (1 - lambda) * h_ij
    for u, v, data in G.edges(data=True):
        data['cost'] = lmbda * data['distance'] + (1 - lmbda) * data['heat']

    # Solve shortest path for current lambda weighting
    path = nx.shortest_path(G, source="MU", target="Noble", weight='cost')
    
    # Calculate non-weighted totals for this path choice
    total_dist = sum(G[u][v]['distance'] for u, v in zip(path[:-1], path[1:]))
    total_heat = sum(G[u][v]['heat'] for u, v in zip(path[:-1], path[1:]))
    
    path_name = " -> ".join(path)
    pareto_dict[path_name] = (total_dist, total_heat)

# ---------------------------------------------------------
# 3. Export Static Plot (PNG) via Matplotlib
# ---------------------------------------------------------
plt.figure(figsize=(9, 5))

for path_name, (dist, heat) in pareto_dict.items():
    plt.scatter(dist, heat, s=120, label=path_name, zorder=3)

sorted_points = sorted(pareto_dict.values(), key=lambda x: x[0])
plt.plot([p[0] for p in sorted_points], [p[1] for p in sorted_points], 
         linestyle='--', color='gray', zorder=2)

plt.title("ASU Route Optimization: Distance vs. Heat Exposure", fontsize=12)
plt.xlabel("Total Distance (Meters) → [Minimizing]", fontsize=10)
plt.ylabel("Total Heat Exposure (°F · meters) → [Minimizing]", fontsize=10)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc="upper right", fontsize=8)
plt.tight_layout()

# Save plot directly to project folder
output_png = "pareto_front.png"
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.close()
print(f"Static plot saved to: {output_png}")

# ---------------------------------------------------------
# 4. Export Interactive Web Plot (HTML) via Plotly
# ---------------------------------------------------------
fig = go.Figure()

# Add connecting dashed trade-off line
fig.add_trace(go.Scatter(
    x=[p[0] for p in sorted_points],
    y=[p[1] for p in sorted_points],
    mode='lines',
    line=dict(dash='dash', color='gray'),
    showlegend=False
))

# Add route points
for path_name, (dist, heat) in pareto_dict.items():
    fig.add_trace(go.Scatter(
        x=[dist],
        y=[heat],
        mode='markers',
        marker=dict(size=14),
        name=path_name,
        hovertemplate=f"<b>Route:</b> {path_name}<br><b>Distance:</b> %{{x}} m<br><b>Heat Exposure:</b> %{{y}} °F·m<extra></extra>"
    ))

fig.update_layout(
    title="ASU Route Optimization: Distance vs. Heat Exposure (Interactive)",
    xaxis_title="Total Distance (Meters)",
    yaxis_title="Total Heat Exposure (°F · meters)",
    template="plotly_white"
)

output_html = "pareto_front.html"
fig.write_html(output_html)
print(f"Interactive HTML plot saved to: {output_html}")