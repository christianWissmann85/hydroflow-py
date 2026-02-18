"""Tutorial: Pump Scheduling with Controls.

This tutorial demonstrates how to:
- Add TimeControl and ConditionalControl to a pump
- Compare simulations with and without controls
- Inspect pressure differences between scenarios
- Plot results side by side

Requirements
------------
pip install hydroflow-py[all]
"""

from __future__ import annotations

# %% [markdown]
# # Tutorial 3: Pump Scheduling
#
# We'll build a pumped distribution system, then add controls:
# 1. A **time control** that turns the pump off at night (22:00)
# 2. A **conditional control** that turns it back on when the tank
#    level drops below 2.0 m
#
# We compare pressures with and without these controls.

# %% Build the base network (no controls)
from hydroflow.network import WaterNetwork

def build_network(name: str) -> WaterNetwork:
    """Build the base pump-tank network."""
    net = WaterNetwork(name)

    # Source
    net.add_reservoir("R1", head=30.0, coordinates=(0.0, 50.0))

    # Tank on the hill
    net.add_tank(
        "T1",
        elevation=50.0,
        init_level=3.0,
        min_level=0.5,
        max_level=5.0,
        diameter=10.0,
        coordinates=(200.0, 100.0),
    )

    # Demand junctions
    net.add_junction("J1", elevation=40.0, base_demand=0.003,
                     coordinates=(100.0, 50.0))
    net.add_junction("J2", elevation=35.0, base_demand=0.008,
                     coordinates=(300.0, 50.0))

    # Pump from reservoir to junction
    net.add_pump("PMP1", "R1", "J1", power=15000.0)

    # Pipes
    net.add_pipe("P1", "J1", "T1", length=300, diameter=0.25, roughness="ductile_iron")
    net.add_pipe("P2", "T1", "J2", length=400, diameter=0.2, roughness="pvc")

    return net

# %% Scenario 1: No controls (pump runs 24/7)
from hydroflow.network.simulate import simulate

net_always_on = build_network("Always-On Pump")
print(net_always_on)

results_on = simulate(net_always_on, duration="24h", timestep="1h")
print(f"\nScenario 1 (no controls): {results_on}")

# %% Scenario 2: Add pump scheduling controls
net_scheduled = build_network("Scheduled Pump")

# Turn pump OFF at 22:00
net_scheduled.add_time_control("PMP1", status="CLOSED", at="22:00")

# Turn pump back ON when tank level drops below 2.0 m
net_scheduled.add_conditional_control(
    "PMP1",
    status="OPEN",
    condition=("T1", "level", "<", 2.0),
)

results_sched = simulate(net_scheduled, duration="24h", timestep="1h")
print(f"\nScenario 2 (scheduled): {results_sched}")

# %% Compare pressures at J2 (the downstream demand node)
print("\n--- Pressure at J2: Always-On vs. Scheduled ---")
print(f"{'Time':>15}  {'Always-On':>10}  {'Scheduled':>10}  {'Diff':>8}")
print(f"{'-'*15}  {'-'*10}  {'-'*10}  {'-'*8}")

for i in range(len(results_on.pressures)):
    t = results_on.pressures.index[i]
    p_on = results_on.pressures["J2"].iloc[i]
    p_sched = results_sched.pressures["J2"].iloc[i]
    diff = p_sched - p_on
    print(f"{str(t):>15}  {p_on:10.2f}  {p_sched:10.2f}  {diff:+8.2f}")

# %% Health checks for both scenarios
print("\n--- Health Check: Always-On ---")
issues = results_on.health_check()
if issues:
    for issue in issues:
        print(f"  - {issue}")
else:
    print("  All clear!")

print("\n--- Health Check: Scheduled ---")
issues = results_sched.health_check()
if issues:
    for issue in issues:
        print(f"  - {issue}")
else:
    print("  All clear!")

# %% Plot both networks side by side
import matplotlib.pyplot as plt

from hydroflow.network.plot import plot_network

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Extract pressures at hour 12 for coloring
p_on_dict = dict(results_on.pressures.iloc[12])
p_sched_dict = dict(results_sched.pressures.iloc[12])

plot_network(
    net_always_on,
    node_attribute=p_on_dict,
    title="Always-On at Hour 12",
    ax=ax1,
)
plot_network(
    net_scheduled,
    node_attribute=p_sched_dict,
    title="Scheduled at Hour 12",
    ax=ax2,
)

fig.suptitle("Pump Scheduling: Pressure Comparison", fontsize=14)
fig.tight_layout()
print("\nSide-by-side plot generated — close the window to exit.")
plt.show()
