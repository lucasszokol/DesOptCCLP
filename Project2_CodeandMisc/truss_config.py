"""Editable input data for the example aircraft-spar truss.

Replace these lists to analyze another 2D truss. Node numbers are the zero-based
positions in NODES. For example, node 0 is NODES[0].
"""

# Each tuple gives one node as (x coordinate, y coordinate).
# The example has a lower and upper node at seven spanwise stations.
NODES = [
    (0.0, 0.0),  # Node 0: lower root.
    (0.0, 1.0),  # Node 1: upper root.
    (1.0, 0.0),  # Node 2.
    (1.0, 1.0),  # Node 3.
    (2.0, 0.0),  # Node 4.
    (2.0, 1.0),  # Node 5.
    (3.0, 0.0),  # Node 6.
    (3.0, 1.0),  # Node 7.
    (4.0, 0.0),  # Node 8.
    (4.0, 1.0),  # Node 9.
    (5.0, 0.0),  # Node 10.
    (5.0, 1.0),  # Node 11.
    (6.0, 0.0),  # Node 12: lower tip.
    (6.0, 1.0),  # Node 13: upper tip.
]

# Each tuple gives (start node, end node, stiffness group).
# A "soft" member has k=1. A "stiff" member has k=r in the ratio sweep.
MEMBERS = [
    # Lower chord members.
    (0, 2, "stiff"),
    (2, 4, "stiff"),
    (4, 6, "stiff"),
    (6, 8, "stiff"),
    (8, 10, "stiff"),
    (10, 12, "stiff"),
    # Upper chord members.
    (1, 3, "stiff"),
    (3, 5, "stiff"),
    (5, 7, "stiff"),
    (7, 9, "stiff"),
    (9, 11, "stiff"),
    (11, 13, "stiff"),
    # Alternating Warren diagonals.
    (0, 3, "soft"),
    (3, 4, "soft"),
    (4, 7, "soft"),
    (7, 8, "soft"),
    (8, 11, "soft"),
    (11, 12, "soft"),
    # Vertical posts.
    (0, 1, "stiff"),
    (2, 3, "stiff"),
    (4, 5, "stiff"),
    (6, 7, "stiff"),
    (8, 9, "stiff"),
    (10, 11, "stiff"),
    (12, 13, "stiff"),
]

# Each tuple gives (node, fix horizontal displacement, fix vertical displacement).
# Fixing both root nodes removes horizontal, vertical, and rotational rigid motion.
SUPPORTS = [
    (0, True, True),
    (1, True, True),
]

# Each tuple gives (node, horizontal force, vertical force).
# Negative vertical force points downward. The total downward tip load is one.
LOADS = [
    (12, 0.0, -0.5),
    (13, 0.0, -0.5),
]
