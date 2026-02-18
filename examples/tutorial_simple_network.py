"""Tutorial: Build and Visualize a Simple Gravity-Fed Network.

This tutorial demonstrates how to:
- Build a 3-node gravity-fed water distribution network
- Simulate 24 hours of operation
- Inspect pressures and flows
- Plot the network colored by pressure

Requirements
------------
pip install hydroflow-py[all]
"""

from __future__ import annotations

# %% [markdown]
# # Tutorial 1: Simple Gravity-Fed Network
#
# We'll build a small network: one reservoir feeding two junctions
# through gravity. Then we'll simulate it and see the results.

# %% Build the network
from hydroflow.network import WaterNetwork

net = WaterNetwork("Simple Gravity Network")

# A reservoir sits on a hill at 125 m head.
# We give it coordinates for plotting.
net.add_reservoir("R1", head=125.0, coordinates=(0.0, 100.0))

# Two demand junctions downhill
net.add_junction("J1", elevation=100.0, base_demand=0.005,
                 coordinates=(200.0, 100.0))
net.add_junction("J2", elevation=95.0, base_demand=0.010,
                 coordinates=(400.0, 100.0))

# Connect them with ductile iron pipes
net.add_pipe("P1", "R1", "J1", length=500, diameter=0.3, roughness="ductile_iron")
net.add_pipe("P2", "J1", "J2", length=400, diameter=0.25, roughness="ductile_iron")

print(net)

# %% Validate the network
warnings = net.validate()
print(f"\nValidation returned {len(warnings)} warning(s):")
for w in warnings:
    print(f"  - {w}")

# %% Simulate 24 hours
from hydroflow.network.simulate import simulate

results = simulate(net, duration="24h", timestep="1h")
print(f"\n{results}")

# %% Inspect pressures at the first timestep
print("\nPressures at hour 0:")
print(results.pressures.iloc[0])

print("\nPressures at hour 12:")
print(results.pressures.iloc[12])

# %% Inspect flows
print("\nFlow rates at hour 0:")
print(results.flows.iloc[0])

# %% Health check
issues = results.health_check()
if issues:
    print("\nHealth check issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nAll clear — network is healthy!")

# %% Plot the network colored by pressure
import matplotlib.pyplot as plt

from hydroflow.network.plot import plot_network

# Extract pressures at the first timestep as a dict
pressure_dict = dict(results.pressures.iloc[0])

ax = plot_network(
    net,
    node_attribute=pressure_dict,
    node_cmap="RdYlGn",
    title="Pressure at Hour 0 (m)",
)
print("\nPlot generated — close the window to exit.")
plt.show()
