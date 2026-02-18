#!/usr/bin/env python3
"""Example: Build, simulate, and analyze a pipe network with HydroFlow.

This script demonstrates the core workflow for water distribution
network analysis using the ``hydroflow.network`` package.

Requirements
------------
pip install hydroflow-py[epanet]
"""

from __future__ import annotations

from hydroflow.network import WaterNetwork
from hydroflow.network.simulate import simulate

# ── 1. Build the network ─────────────────────────────────────────────

net = WaterNetwork("Tutorial Network")

# Source: a reservoir at 125 m head
net.add_reservoir("R1", head=125.0)

# Junctions (demand nodes)
net.add_junction("J1", elevation=100.0, base_demand=0.005)
net.add_junction("J2", elevation=95.0, base_demand=0.010)
net.add_junction("J3", elevation=90.0, base_demand=0.008)

# Pipes — note the material-based roughness!
net.add_pipe("P1", "R1", "J1", length=500, diameter=0.3, roughness="ductile_iron")
net.add_pipe("P2", "J1", "J2", length=400, diameter=0.25, roughness="ductile_iron")
net.add_pipe("P3", "J2", "J3", length=300, diameter=0.2, roughness="pvc")

print(net)
# WaterNetwork('Tutorial Network', nodes=4, links=3)

# ── 2. Validate ──────────────────────────────────────────────────────

warnings = net.validate()
for w in warnings:
    print(f"  Warning: {w}")

# ── 3. Simulate ──────────────────────────────────────────────────────

results = simulate(net, duration="24h", timestep="1h")
print(results)

# ── 4. Inspect results ───────────────────────────────────────────────

print("\nPressures at hour 12:")
print(results.pressures.iloc[12])

print("\nFlow rates at hour 0:")
print(results.flows.iloc[0])

# ── 5. Health check ──────────────────────────────────────────────────

issues = results.health_check()
if issues:
    print("\nHealth check issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nNetwork is healthy!")
