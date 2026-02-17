"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    hydroflow — The Dream API                           ║
║                                                                        ║
║   "Write the code you wish existed, then work backwards."              ║
║                                                                        ║
║   This file is NOT runnable code. It's our north star — the API we     ║
║   want to build. Every example here represents a real engineering      ║
║   workflow that is currently painful, fragmented, or impossible.        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 0: CORE ENGINEERING CALCULATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# THE GAP: There is NO Python library for everyday hydraulic design
# calculations. Engineers currently use Excel spreadsheets, HEC tools
# with GUIs, or hand calculations. Libraries like ChannelFlowLib and
# PyFlo are dead. This layer alone would be a game-changer.
#
# Dependencies: numpy, scipy only. Zero-dependency core.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import hydroflow as hf

# ── Open Channel Flow ─────────────────────────────────────────────────

# Manning's equation — the bread and butter of hydraulic engineering
# Today: engineers look up roughness in a PDF table, plug into Excel
# Tomorrow:

channel = hf.TrapezoidalChannel(
    bottom_width=3.0,       # meters
    side_slope=2.0,         # horizontal:vertical
    slope=0.001,            # m/m
    roughness="concrete",   # auto-lookup! No memorizing n=0.013
)

# Solve for any unknown — the library figures out which equation form to use
flow = channel.normal_flow(depth=1.5)          # Q given depth
depth = channel.normal_depth(flow=5.0)         # depth given Q (iterative)
critical = channel.critical_depth(flow=5.0)    # critical depth
froude = channel.froude_number(depth=1.5)      # flow regime check

# Is this supercritical or subcritical? Engineers ask this constantly.
print(channel.flow_regime(depth=1.5))
# >>> FlowRegime.SUBCRITICAL (Fr=0.42)

# Different channel shapes — same clean API
pipe = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="corrugated_metal")
rect = hf.RectangularChannel(width=2.0, slope=0.002, roughness="earth_clean")

# Capacity check — "will this pipe handle a 10-year storm?"
print(pipe.full_flow_capacity())
# >>> 0.34 m³/s

# ── Culvert Hydraulics ───────────────────────────────────────────────
# THE GAP: HY-8 (FHWA culvert analysis) has no Python equivalent. None.

culvert = hf.Culvert(
    shape="circular",
    diameter=1.2,           # meters
    length=30,              # meters
    slope=0.02,
    material="concrete",
    inlet="square_edge",    # inlet type matters enormously
)

# The culvert automatically checks both inlet and outlet control
result = culvert.analyze(
    headwater=3.0,          # upstream depth
    tailwater=0.5,          # downstream depth
)
print(result.flow)                # discharge
print(result.control)             # "INLET_CONTROL" or "OUTLET_CONTROL"
print(result.headwater_ratio)     # HW/D — engineers live by this number

# Performance curve — headwater vs. flow for a range
curve = culvert.performance_curve(hw_range=(0.5, 5.0), steps=50)
curve.plot()  # matplotlib figure, publication-ready

# ── Hydrology: Rainfall-Runoff ───────────────────────────────────────
# THE GAP: Every consulting firm does this in Excel. Every. Single. One.

# Design storm from IDF curve
storm = hf.DesignStorm.from_idf(
    location="Austin, TX",          # auto-fetch NOAA Atlas 14!
    return_period=25,               # years
    duration="24h",
    method="SCS_Type_II",           # standard temporal distribution
)

# Or define manually
storm = hf.DesignStorm.from_table(
    durations=["5min", "10min", "15min", "30min", "1h", "2h"],
    depths=[0.5, 0.8, 1.0, 1.5, 2.0, 2.8],  # inches or mm
    units="inches",
)

# Watershed/catchment properties
watershed = hf.Watershed(
    area=2.5,                       # km² (or acres, auto-converts)
    curve_number=75,                # SCS CN — engineers know this by heart
    time_of_concentration="45min",  # or compute it:
)

# Time of concentration — multiple methods, engineers always compare
tc = hf.time_of_concentration(
    method="kirpich",               # or "faa", "nrcs_lag", "kerby_kirpich"
    length=1200,                    # flow path length (m)
    slope=0.03,                     # average slope
)

# Rational Method — the simplest rainfall-runoff model
# "Every civil engineer learns this in university, uses it for 40 years"
peak_flow = hf.rational_method(
    C=0.65,                         # runoff coefficient
    intensity=storm.intensity_at(tc),  # mm/hr at time of concentration
    area=watershed.area,
)
print(f"Peak flow: {peak_flow:.2f} m³/s")

# SCS Unit Hydrograph — the step up from rational method
hydrograph = hf.scs_unit_hydrograph(
    watershed=watershed,
    storm=storm,
)
hydrograph.plot()                   # clean, labeled, engineering-standard
print(hydrograph.peak_flow)         # m³/s
print(hydrograph.peak_time)         # time to peak
print(hydrograph.volume)            # total runoff volume

# ── Detention Pond Routing ───────────────────────────────────────────
# THE GAP: Modified Puls method in Excel is an absolute nightmare of
# circular references. This should be ONE function call.

pond = hf.DetentionPond(
    stage_storage={                 # stage (m) : storage (m³)
        0.0: 0,
        0.5: 500,
        1.0: 1500,
        1.5: 3000,
        2.0: 5500,
    },
    outlet=hf.Orifice(diameter=0.3, invert=0.0) + hf.Weir(length=3.0, crest=1.5),
)

routed = pond.route(inflow=hydrograph)
print(routed.peak_reduction)        # "62% peak flow reduction"
print(routed.max_stage)             # maximum water level in pond
routed.plot(show_inflow=True)       # inflow vs outflow hydrograph


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1: SOLVER WRAPPERS (Clean APIs over EPANET, SWMM, MODFLOW)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# THE GAP: Existing wrappers (WNTR, PySWMM, FloPy) mirror the solver's
# mental model. We mirror the ENGINEER's mental model.
#
# Key differences from existing tools:
#   - Human-readable time ("24h" not 86400 seconds)
#   - Material/roughness auto-lookup
#   - Errors that EXPLAIN what went wrong and suggest fixes
#   - Immutable simulation (no pickle hacks for parameter sweeps)
#   - Results always as DataFrames
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Pipe Networks (EPANET backend) ───────────────────────────────────

net = hf.WaterNetwork("Springfield Distribution")

# Add components — material lookup is automatic
reservoir = net.add_reservoir("Lake_Springfield", head=250)
tank = net.add_tank("Tower_1", elevation=220, diameter=10, min_level=2, max_level=8)

house_a = net.add_junction("Residential_A", elevation=200, demand=15)  # L/s
factory = net.add_junction("Factory", elevation=195, demand=50)

# Connect — the library handles ID references, roughness coefficients
net.connect(reservoir, house_a, length=2000, diameter=300, material="ductile_iron")
net.connect(house_a, factory, length=500, diameter=200, material="PVC")
net.connect(reservoir, tank, length=1500, diameter=400, material="steel")
net.connect(tank, factory, length=800, diameter=250, material="PVC")

# Pumps — with human-readable curve definition
net.add_pump("Main_Pump", source=reservoir, target=tank,
             curve=[(0, 50), (100, 40), (200, 20)])  # (flow L/s, head m)

# Controls — readable, not six lines of object composition
net.add_rule("Fill tank at night",
             condition="tank.Tower_1.level < 3 AND time.hour >= 22",
             action="pump.Main_Pump.status = ON")

net.add_rule("Stop filling when full",
             condition="tank.Tower_1.level > 7",
             action="pump.Main_Pump.status = OFF")

# Simulate — with human-readable duration
results = net.simulate(duration="48h", timestep="15min")

# Results — always DataFrames, always labeled
print(results.pressures)        # DataFrame: time × node names
print(results.flows)            # DataFrame: time × pipe names
print(results.velocities)

# Health check — instant engineering review
report = results.health_check()
# >>> ⚠ WARNING: Negative pressure at 'Residential_A' from 14:00-16:00
# >>> ⚠ WARNING: Velocity > 3 m/s in pipe 'reservoir→house_a' (peak: 3.4 m/s)
# >>> ✓ All tanks recovered within 24h cycle

# Error handling — ACTUALLY HELPFUL (unlike WNTR's "Error 203")
try:
    results = net.simulate()
except hf.SimulationError as e:
    print(e)
    # >>> SimulationError: Disconnected junction 'Factory'
    # >>>   → Factory has no path to any source (reservoir or tank)
    # >>>   → Did you mean to connect it to 'Tower_1' (nearest node, 800m)?

# ── Stormwater / Urban Drainage (SWMM backend) ──────────────────────

city = hf.StormwaterModel("Downtown Austin")

# Subcatchments — with sensible defaults, not 15 parameters
block_a = city.add_subcatchment("Block_A",
    area=5.0,                   # hectares
    imperviousness=0.7,         # fraction
    slope=0.02,
    land_use="commercial",      # auto-sets infiltration, roughness, depression storage
)

block_b = city.add_subcatchment("Block_B",
    area=8.0,
    imperviousness=0.3,
    slope=0.01,
    land_use="residential_medium",
)

# Drainage system
outfall = city.add_outfall("River_Colorado", elevation=140)

city.connect(block_a, block_b, shape="circular", diameter=600)  # mm
city.connect(block_b, outfall, shape="box", width=1200, height=900)

# Apply design storm (reuse from Layer 0!)
city.apply_rainfall(storm)

# Simulate
results = city.simulate()

# Key results engineers actually need
print(results.peak_flow_at("River_Colorado"))       # peak discharge
print(results.max_depth_at("Block_A"))              # max ponding
print(results.flooding_volume())                    # total flooding
print(results.time_to_peak())                       # hydrograph timing

# ── Groundwater (MODFLOW backend) ────────────────────────────────────

# Instead of FloPy's "ModflowGwfnpf(gwf, icelltype=[1,0,0], k=[10,1,0.1])"
# We write what a hydrogeologist actually thinks:

aquifer = hf.GroundwaterModel("Central_Texas_Aquifer")

aquifer.set_grid(rows=50, cols=50, cell_size=100)   # 100m cells

# Define layers by what they ARE, not by Fortran variable names
aquifer.add_layer("Alluvium",       thickness=20, K=10.0,  type="unconfined")
aquifer.add_layer("Clay_Aquitard",  thickness=5,  K=0.01,  type="confined")
aquifer.add_layer("Edwards_Limestone", thickness=50, K=5.0, type="confined")

# Boundary conditions — named, not package abbreviations
aquifer.add_river("Colorado_River", stage=150, conductance=500,
                  cells=aquifer.cells_along(y=2500))

aquifer.add_well("Municipal_Well_1", location=(1200, 3400),
                 layer="Edwards_Limestone", rate=-500)  # m³/day extraction

aquifer.add_recharge(rate=0.001)  # m/day, applied to top layer

# Simulate — human-readable time, not Fortran stress periods
results = aquifer.simulate(
    duration="10 years",
    output_every="1 month",
)

# Results — what hydrogeologists actually ask
print(results.head_at("Municipal_Well_1"))          # head timeseries
print(results.drawdown_at("Municipal_Well_1"))      # drawdown from initial
print(results.water_budget())                       # in/out summary
results.plot_head_map(layer="Edwards_Limestone", time="5 years")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2: WORKFLOWS & COUPLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# THE GAP: In real projects, models are CHAINED. Rainfall feeds drainage
# feeds rivers feeds groundwater. Today this requires manual data
# transfer between completely different tools. Nobody has solved this.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# The dream: a complete site development analysis in one script

project = hf.Workflow("Riverside_Development")

# Step 1: Define the storm
storm = hf.DesignStorm.from_idf("Austin, TX", return_period=100, duration="24h")

# Step 2: Pre-development hydrology
pre_dev = hf.Watershed(area=50, curve_number=65, tc="2h")
pre_hydrograph = hf.scs_unit_hydrograph(pre_dev, storm)

# Step 3: Post-development drainage model
post_dev = hf.StormwaterModel("Post_Development")
# ... define subcatchments, pipes, ponds ...

# Step 4: Downstream river impact
river = hf.RiverModel("Colorado_Reach")
river.load_cross_sections("survey_data.csv")

# Chain them together — output of one becomes input of next
project.add_step("rainfall", storm)
project.add_step("drainage", post_dev, receives={"rainfall": "storm"})
project.add_step("detention", pond, receives={"drainage": "outflow"})
project.add_step("river", river, receives={"detention": "outflow"})

# Run the entire chain
results = project.run()

# Compare pre vs post development
comparison = hf.compare(
    pre=pre_hydrograph,
    post=results["detention"].outflow,
)
print(comparison)
# >>> Pre-development peak:  12.3 m³/s at 08:45
# >>> Post-development peak: 11.8 m³/s at 09:15  ✓ (4% reduction)
# >>> Post-development volume: +15% (requires additional storage)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 3: AI & OPTIMIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# THE GAP: This is where proprietary software charges $$$$ for "add-on
# optimization modules." In Python, scipy.optimize is free — but nobody
# has built the bridge between optimizers and water engineering solvers.
#
# Also: THIS is what makes the library AI-native. An LLM can write
# optimization code if the API is clean and structured.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Pipe Network Optimization ────────────────────────────────────────

# "Find the cheapest pipe diameters that maintain 20m pressure everywhere"
# In WNTR: write 50 lines of pickle-based loops
# In hydroflow:

from hydroflow.optimize import minimize_cost

optimal = minimize_cost(
    network=net,
    variables={
        "reservoir→house_a": hf.DiameterRange(150, 500),
        "house_a→factory":   hf.DiameterRange(100, 300),
    },
    constraints={
        "min_pressure": 20,         # meters, at all nodes
        "max_velocity": 3.0,        # m/s, in all pipes
    },
    catalog="standard_metric",      # only real purchasable pipe sizes
)

print(optimal.diameters)            # {pipe_name: optimal_diameter}
print(optimal.total_cost)           # estimated material cost
print(optimal.iterations)           # how many simulations it took
optimal.compare_to(net)             # side-by-side with original design

# ── Parameter Sweep ──────────────────────────────────────────────────

# "What happens to flooding if imperviousness increases from 30% to 90%?"
# Classic climate/urbanization sensitivity study

sweep = hf.ParameterSweep(
    model=city,
    parameter="Block_B.imperviousness",
    values=hf.linspace(0.3, 0.9, 13),  # 13 steps from 30% to 90%
)

# Runs all simulations (parallel by default!)
results = sweep.run()

# Results as a clean DataFrame
print(results.summary)
# >>>   imperviousness  peak_flow  total_flooding  time_to_peak
# >>>   0.30            2.1        0               45min
# >>>   0.35            2.4        0               42min
# >>>   ...
# >>>   0.90            8.7        1250 m³         28min

results.plot(x="imperviousness", y="peak_flow")

# ── Calibration ──────────────────────────────────────────────────────

# "Match my model to observed field data"
# Today: weeks of manual trial-and-error in a GUI
# Tomorrow:

calibration = hf.calibrate(
    model=aquifer,
    observed={
        "Municipal_Well_1": observed_heads_df,   # pandas DataFrame
        "Monitoring_Well_A": observed_heads_df_2,
    },
    parameters={
        "Alluvium.K":       (1.0, 100.0),       # bounds
        "Clay_Aquitard.K":  (0.001, 0.1),
        "recharge.rate":    (0.0001, 0.005),
    },
    metric="rmse",          # or "nse" (Nash-Sutcliffe), "pbias"
    method="differential_evolution",  # global optimizer
)

print(calibration.best_params)
print(calibration.rmse)
calibration.plot_fit()              # observed vs simulated at each well

# ── AI-Friendly: Structured I/O for LLM Agents ──────────────────────

# Export model as JSON schema — an LLM can read this and modify it
schema = net.to_schema()
# Returns structured dict with types, ranges, and descriptions
# An AI agent can generate valid model modifications from this

# Problem definition — structured enough for an AI to solve
problem = hf.Problem(
    model=net,
    objective="minimize_cost",
    constraints={"min_pressure": 20, "max_velocity": 2.5},
    variables={"pipe_diameters": "all"},
)

# The problem serializes to JSON — perfect for LLM tool-use
print(problem.to_json())
# {
#   "objective": "minimize_cost",
#   "variables": [
#     {"name": "pipe_reservoir→house_a_diameter", "type": "float",
#      "bounds": [100, 600], "unit": "mm"},
#     ...
#   ],
#   "constraints": [
#     {"name": "min_pressure", "type": ">=", "value": 20, "unit": "m"},
#     ...
#   ]
# }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 4: REPORTING (The Proprietary Killer Feature)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# THE GAP: Proprietary tools generate "one-click" regulatory reports.
# Open source tools give you raw numbers. The report generation is
# what makes clients pay $20k/year.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

report = hf.Report("Riverside Development — Drainage Analysis")

report.add_section("Design Storm",
    storm.summary(),
    storm.plot(),
)

report.add_section("Pre-Development Hydrology",
    pre_hydrograph.summary(),
    pre_hydrograph.plot(),
)

report.add_section("Post-Development Analysis",
    results["drainage"].summary(),
    comparison.table(),
    comparison.plot(),
)

report.add_section("Detention Pond Design",
    pond.summary(),
    routed.plot(show_inflow=True),
    f"Peak reduction: {routed.peak_reduction:.0%}",
)

# Export — what the client actually receives
report.to_pdf("drainage_report.pdf")        # formatted, professional
report.to_html("drainage_report.html")       # interactive
report.to_markdown("drainage_report.md")     # for version control


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIT HANDLING — A Cross-Cutting Concern
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# US engineers use feet, inches, cfs, acres. Everyone else uses metric.
# The library handles this transparently.

hf.set_units("imperial")  # or "metric" (default)

# Now all inputs/outputs are in imperial
channel = hf.TrapezoidalChannel(
    bottom_width=10,        # feet (not meters)
    side_slope=2.0,
    slope=0.001,
    roughness="concrete",
)
flow = channel.normal_flow(depth=5.0)  # returns cfs (not m³/s)

# Or be explicit per-value
channel = hf.TrapezoidalChannel(
    bottom_width=hf.ft(10),
    slope=0.001,
    roughness="concrete",
)
