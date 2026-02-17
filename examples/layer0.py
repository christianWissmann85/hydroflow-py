"""HydroFlow Layer 0 — Complete Capabilities Demo.

Seven real-world engineering workflows that used to require Excel
spreadsheets or $20k/year proprietary software. Each section is a
task a civil/hydraulic engineer might face on any given Tuesday.
"""

import math

import hydroflow as hf

# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 1: Size a roadside drainage ditch
#
# "The county wants a concrete-lined trapezoidal channel to carry
#  the 25-year storm runoff of 21 m³/s. What depth do we need?"
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 1: Roadside Drainage Ditch Design")
print("=" * 70)

hf.set_units("metric")

ditch = hf.TrapezoidalChannel(
    bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="concrete"
)

# Forward: what flow can this ditch carry at 1.5m depth?
Q = ditch.normal_flow(depth=1.5)
print(f"  Capacity at 1.5m depth:  {Q:.2f} m\u00b3/s")

# Inverse: what depth do we need for the design flow?
y_design = ditch.normal_depth(flow=21.0)
print(f"  Required depth for 21 m\u00b3/s: {y_design:.3f} m")

# Is the flow subcritical? (We need subcritical for a ditch.)
yc = ditch.critical_depth(flow=21.0)
Fr = ditch.froude_number(depth=y_design)
regime = ditch.flow_regime(depth=y_design)
print(f"  Critical depth:  {yc:.3f} m")
print(f"  Froude number:   {Fr:.3f}  ->  {regime.value}")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 2: Storm sewer pipe sizing
#
# "Will a 600mm concrete pipe handle 0.4 m³/s on a 0.5% slope?
#  What's the flow depth? Is it surcharged?"
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 2: Storm Sewer Pipe Check")
print("=" * 70)

pipe = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="concrete")

Q_full = pipe.full_flow_capacity()
Q_max = pipe.max_flow_capacity()
print("  600mm pipe on 0.5% slope:")
print(f"    Full-pipe capacity: {Q_full:.3f} m\u00b3/s")
print(f"    True max capacity:  {Q_max:.3f} m\u00b3/s  (at y/D \u2248 0.938)")

Q_check = 0.40
if Q_check <= Q_max:
    y = pipe.normal_depth(flow=Q_check)
    print(f"    Depth for {Q_check} m\u00b3/s:  {y:.3f} m  ({y/0.6:.0%} full)  \u2714 OK")
else:
    print(f"    {Q_check} m\u00b3/s EXCEEDS capacity!  \u2718 Upsize needed")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 3: Imperial mode — verify a textbook example
#
# "Reproduce Chow (1959) Example 6-1 to validate our calcs."
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 3: Textbook Verification (Chow 1959, Ex. 6-1)")
print("=" * 70)

hf.set_units("imperial")

ch_chow = hf.TrapezoidalChannel(
    bottom_width=20, side_slope=1.5, slope=0.0016, roughness=0.025
)
Q_cfs = ch_chow.normal_flow(depth=4.0)
print("  b=20ft, z=1.5, S=0.0016, n=0.025, y=4ft")
print(f"  Computed Q = {Q_cfs:.1f} cfs  (Chow reports ~519 cfs)")

# Roundtrip: recover the depth
y_back = ch_chow.normal_depth(flow=Q_cfs)
print(f"  Depth roundtrip: {y_back:.4f} ft  (should be 4.0000)")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 4: Subdivision hydrology — SCS method
#
# "A 50-hectare suburban watershed (CN=80) receives a 100mm storm.
#  How much runoff? What's the peak discharge? When does it peak?"
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 4: Subdivision Hydrology (SCS Method)")
print("=" * 70)

hf.set_units("metric")

# Step 1: How much rain becomes runoff?
P_mm = 100.0
CN = 80
runoff_mm = hf.scs_runoff_depth(rainfall=P_mm, curve_number=CN)
print(f"  Rainfall: {P_mm:.0f} mm, CN={CN}")
print(f"  Direct runoff: {runoff_mm:.1f} mm  ({runoff_mm/P_mm:.0%} of rainfall)")

# Step 2: Time of concentration (Kirpich method)
Tc = hf.time_of_concentration(
    method="kirpich", length=hf.ft(4500), slope=0.025
)
print(f"  Time of concentration: {Tc:.1f} min")

# Step 3: Quick peak estimate via Rational Method
Q_rational = hf.rational_method(
    C=0.60,
    intensity=P_mm / (Tc / 60.0),  # approximate intensity (mm/hr)
    area=hf.ha(50),
)
print(f"  Rational Method peak:  {Q_rational:.2f} m\u00b3/s")

# Step 4: Full SCS unit hydrograph for a Type II 24-hour storm
watershed = hf.Watershed(
    area=hf.ha(50), curve_number=CN, time_of_concentration=Tc
)
storm = hf.DesignStorm.from_scs_type2(total_depth=P_mm)
hydrograph = hf.scs_unit_hydrograph(watershed, storm)

print("  SCS Unit Hydrograph:")
print(f"    Peak flow:   {hydrograph.peak_flow:.2f} m\u00b3/s")
print(f"    Time to peak: {hydrograph.peak_time_seconds / 3600:.1f} hours")
print(f"    Total volume: {hydrograph.volume:.0f} m\u00b3")

# Sanity check: volume = runoff_depth * area
expected_vol = (runoff_mm / 1000.0) * (50 * 10000)  # 50 ha in m²
print(f"    Expected vol:  {expected_vol:.0f} m\u00b3  (runoff x area)")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 5: Detention pond design
#
# "Route the hydrograph through a pond with a weir + orifice outlet.
#  Does it reduce the peak enough to meet the local ordinance?"
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 5: Detention Pond Routing")
print("=" * 70)

# Outlet structure: low-level orifice + emergency weir
low_orifice = hf.Orifice(diameter=0.3, invert=0.0, Cd=0.61)
overflow_weir = hf.RectangularWeir(length=3.0, crest=2.0, Cw=1.84)
outlet = low_orifice + overflow_weir

# Show combined stage-discharge
print("  Outlet stage-discharge table:")
for stage in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    Q_out = outlet.discharge(stage=stage)
    print(f"    Stage {stage:.1f}m  ->  Q = {Q_out:.3f} m\u00b3/s")

# Route the hydrograph from Workflow 4 through the pond
pond = hf.DetentionPond(
    stages=[0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    storages=[0, 500, 2000, 5000, 10000, 17000, 26000, 37000],
    outlet=outlet,
)
# Use hydrograph from Workflow 4
dt_s = float(hydrograph.times_seconds[1] - hydrograph.times_seconds[0])
result = pond.route(hydrograph, dt=dt_s)

print("\n  Routing results:")
print(f"    Peak inflow:     {result.peak_inflow:.2f} m\u00b3/s")
print(f"    Peak outflow:    {result.peak_outflow:.2f} m\u00b3/s")
print(f"    Peak reduction:  {result.peak_reduction:.0%}")
print(f"    Max pond stage:  {result.max_stage:.2f} m")
print(f"    Time to peak:    {result.time_to_peak_outflow / 3600:.1f} hours")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 6: Road crossing culvert analysis
#
# "Size a culvert under a county road. The design flow is 3 m³/s.
#  What headwater does a 900mm concrete pipe produce?"
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 6: Culvert Sizing (FHWA HDS-5)")
print("=" * 70)

culvert = hf.Culvert(
    diameter=0.9,
    length=25.0,
    slope=0.015,
    roughness="concrete",
    inlet="groove_end",
)

Q_design = 3.0
r = culvert.analyze(flow=Q_design, tailwater=0.3)
print("  900mm concrete culvert, 25m long, 1.5% slope, groove-end inlet:")
print(f"    Design flow:     {r.flow:.1f} m\u00b3/s")
print(f"    Headwater:       {r.headwater:.3f} m")
print(f"    HW/D ratio:      {r.headwater_ratio:.2f}")
print(f"    Control:         {r.control}")
print(f"    Barrel velocity: {r.velocity:.2f} m/s")
print(f"    HW (inlet ctl):  {r.hw_inlet:.3f} m")
print(f"    HW (outlet ctl): {r.hw_outlet:.3f} m")

# Performance curve: headwater vs. flow
print("\n  Performance curve:")
col_flow = "Flow (m\u00b3/s)"
print(f"    {col_flow:>12}  {'HW (m)':>8}  {'HW/D':>6}  {'Control':>16}")
print(f"    {'-' * 12}  {'-' * 8}  {'-' * 6}  {'-' * 16}")
for pt in culvert.performance_curve(flow_range=(0.5, 5.0), steps=10):
    print(f"    {pt.flow:12.2f}  {pt.headwater:8.3f}  {pt.headwater_ratio:6.2f}  {pt.control:>16}")

# Compare inlet types
print(f"\n  Inlet comparison at Q={Q_design} m\u00b3/s:")
for inlet_type in ["square_edge", "groove_end", "beveled", "projecting"]:
    c = hf.Culvert(
        diameter=0.9, length=25.0, slope=0.015,
        roughness="concrete", inlet=inlet_type,
    )
    res = c.analyze(flow=Q_design, tailwater=0.3)
    print(f"    {inlet_type:<14}  HW = {res.headwater:.3f}m  (HW/D = {res.headwater_ratio:.2f})")
print()


# ════════════════════════════════════════════════════════════════════════
# WORKFLOW 7: Water main design — pressure pipe
#
# "A 300mm ductile iron water main runs 500m. What's the head loss
#  at 0.05 m³/s? Include fittings: 2 elbows, 1 tee, 1 gate valve."
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("WORKFLOW 7: Water Main Head Loss")
print("=" * 70)

# Friction losses — compare two methods
dw = hf.darcy_weisbach(
    flow=0.05, diameter=0.3, length=500.0, roughness_mm=0.26  # ductile iron
)
hw_loss = hf.hazen_williams(
    flow=0.05, diameter=0.3, length=500.0, C="ductile_iron_new"
)

print("  300mm ductile iron main, 500m, Q=0.05 m\u00b3/s:")
print("    Darcy-Weisbach:")
print(f"      Head loss:  {dw.head_loss:.3f} m")
print(f"      Velocity:   {dw.velocity:.3f} m/s")
print(f"      Re:         {dw.reynolds:,.0f}")
print(f"      f:          {dw.friction_factor_value:.5f}")
print("    Hazen-Williams (C=140):")
print(f"      Head loss:  {hw_loss:.3f} m")

# Minor losses — the fittings
V = dw.velocity  # reuse velocity from Darcy-Weisbach
fittings = [
    ("90_elbow", 2),
    ("tee_through", 1),
    ("gate_valve_open", 1),
]
total_minor = 0.0
print(f"\n    Minor losses (V = {V:.3f} m/s):")
for fitting, count in fittings:
    K = hf.MINOR_LOSS_K[fitting]
    hm = hf.minor_loss(velocity=V, K=fitting)
    total_minor += hm * count
    print(f"      {count}x {fitting:<20}  K={K:.1f}  h_m={hm:.4f}m  x{count} = {hm*count:.4f}m")

total_head_loss = dw.head_loss + total_minor
print("\n    Total system head loss:")
print(f"      Friction:  {dw.head_loss:.3f} m")
print(f"      Fittings:  {total_minor:.3f} m")
print(f"      TOTAL:     {total_head_loss:.3f} m")
print()


# ════════════════════════════════════════════════════════════════════════
# BONUS: Hydraulic jump below a dam spillway
# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("BONUS: Hydraulic Jump (Energy Dissipation)")
print("=" * 70)

# Supercritical flow at the base of a spillway
y1 = 0.25  # m (shallow, fast)
b = 5.0    # m (channel width)
Fr1 = 4.5  # strong jump
V1 = Fr1 * math.sqrt(9.80665 * y1)
Q_jump = V1 * b * y1

jump = hf.hydraulic_jump(flow=Q_jump, upstream_depth=y1, width=b)
print(f"  Incoming: y1={y1}m, Fr={jump.froude_upstream:.1f}, V={V1:.2f} m/s")
print(f"  Sequent depth:  y2 = {jump.sequent_depth:.3f} m")
print(f"  Energy loss:    dE = {jump.energy_loss:.3f} m")
print(f"  Downstream Fr:  {jump.froude_downstream:.3f}")
print(f"  Depth ratio:    y2/y1 = {jump.sequent_depth/y1:.1f}")
print()


# ════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("All workflows complete. Every calculation above used to require")
print("a separate Excel spreadsheet or proprietary software license.")
print("Now it's 150 lines of Python.")
print("=" * 70)
