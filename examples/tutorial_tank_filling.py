"""Tutorial: Tank Filling with a Pump.

This tutorial demonstrates how to:
- Build a reservoir-pump-tank topology
- Simulate tank filling over 24 hours
- Monitor tank level time-series
- Run a health check on the results
- Plot the network topology

Requirements
------------
pip install hydroflow-py[all]
"""

from __future__ import annotations

# %% [markdown]
# # Tutorial 2: Tank Filling
#
# A pump pushes water from a low-head reservoir into an elevated
# storage tank. We'll watch the tank fill over 24 hours and check
# if pressures and velocities stay in acceptable ranges.

# %% Build the network
from hydroflow.network import WaterNetwork

net = WaterNetwork("Tank Filling System")

# Source reservoir at low head
net.add_reservoir("R1", head=20.0, coordinates=(0.0, 0.0))

# Elevated storage tank
net.add_tank(
    "T1",
    elevation=50.0,
    init_level=1.0,     # starts almost empty
    min_level=0.5,
    max_level=5.0,
    diameter=10.0,
    coordinates=(200.0, 0.0),
)

# Junction between pump discharge and tank
net.add_junction("J1", elevation=45.0, coordinates=(100.0, 0.0))

# A pump lifts water from the reservoir
net.add_pump("PMP1", "R1", "J1", power=15000.0)

# Pipe from junction to tank
net.add_pipe("P1", "J1", "T1", length=200, diameter=0.2, roughness="pvc")

print(net)

# %% Validate
warnings = net.validate()
print(f"\nValidation: {len(warnings)} warning(s)")
for w in warnings:
    print(f"  - {w}")

# %% Simulate 24 hours
from hydroflow.network.simulate import simulate

results = simulate(net, duration="24h", timestep="1h")
print(f"\n{results}")

# %% Watch the tank level rise
# Tank head = elevation + water level
# We can see it in the heads DataFrame
print("\nTank head over time (first 6 hours):")
print(results.heads["T1"].head(7))

print("\nTank head at end of simulation:")
print(f"  {results.heads['T1'].iloc[-1]:.2f} m")

# %% Pressures at junction J1
print("\nPressure at J1 over time:")
print(results.pressures["J1"])

# %% Health check
issues = results.health_check(min_pressure=0.0, max_velocity=3.0)
if issues:
    print("\nHealth check found issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nSystem is healthy — all pressures and velocities OK!")

# %% Plot the network
from hydroflow.network.plot import plot_network

ax = plot_network(net, title="Tank Filling System")
print("\nPlot generated!")
# plt.show()  # Uncomment for interactive display
