# Layer 0: Core Calculations — Technical Design Document

> **Purpose:** This document contains everything needed to implement Layer 0. Every equation, every edge case, every test value. A developer (human or AI) should be able to implement any module from this doc alone.

---

## Module Structure

```
hydroflow/
├── __init__.py                  # Public API re-exports
├── units.py                     # Unit system (foundation)
├── materials.py                 # Roughness & material lookup (foundation)
├── geometry.py                  # Channel cross-section geometry (foundation)
├── channels.py                  # Open channel flow (Tier 1)
├── hydrology.py                 # Rainfall-runoff: SCS, Rational Method (Tier 2)
├── structures.py                # Culverts, orifices, weirs (Tier 3)
├── routing.py                   # Detention pond routing (Tier 3)
├── pressure.py                  # Pressurized pipe flow (Tier 4)
└── _types.py                    # Shared type aliases, enums
```

Build order follows file dependencies:
```
units.py → materials.py → geometry.py → channels.py → hydrology.py
                                      → structures.py → routing.py
                                      → pressure.py
```

---

## Foundation Module 1: `units.py`

### Design Decision: SI Internally, Convert at Boundaries

All internal calculations use SI units. The Manning's coefficient is always 1.0 — the imperial 1.49 constant never appears in our codebase. This eliminates an entire class of bugs.

**Two-layer architecture:**
- **Public API** (classes): handles unit conversion at construction and return
- **Kernel functions** (prefixed `_`): pure SI math, zero overhead, optimization-safe

### Implementation

```python
# Thread-safe global state
_local = threading.local()

def set_units(system: Literal["metric", "imperial"]) -> None
def get_units() -> str  # defaults to "metric"
```

**Conversion registry:**

| Quantity   | Metric Unit | Imperial Unit | Factor to SI |
|-----------|-------------|---------------|:------------:|
| length    | m           | ft            | 0.3048       |
| area      | m²          | ft²           | 0.09290304   |
| flow      | m³/s        | cfs           | 0.02831685   |
| rainfall  | mm          | in            | 0.0254       |
| catch_area| ha          | acre          | 4046.8564    |
| velocity  | m/s         | ft/s          | 0.3048       |
| volume    | m³          | ft³           | 0.02831685   |

**Explicit per-value tags** via `_Explicit(float)` subclass:

```python
hf.ft(10.0)      # returns _Explicit(10.0, "ft") — a float subclass
hf.m(3.0)        # returns _Explicit(3.0, "m")
hf.inches(5.0)   # returns _Explicit(5.0, "in")
```

`to_si(value, quantity)` checks `isinstance(value, _Explicit)` first; if tagged, uses the tag. Otherwise uses global preference.

**Thread safety:** `threading.local()` so parallel workers in optimization don't interfere.

### Key Functions

```python
def set_units(system: Literal["metric", "imperial"]) -> None
def get_units() -> str
def to_si(value: float, quantity: str) -> float
def from_si(value_si: float, quantity: str) -> float

# Explicit constructors
def ft(v: float) -> _Explicit
def m(v: float) -> _Explicit
def cfs(v: float) -> _Explicit
def cms(v: float) -> _Explicit
def inches(v: float) -> _Explicit
def mm(v: float) -> _Explicit
def acres(v: float) -> _Explicit
def ha(v: float) -> _Explicit
```

---

## Foundation Module 2: `materials.py`

### Purpose

Engineers type `"concrete"`, we return `n = 0.013`. No memorizing coefficients.

### Data Source

Primary: Chow (1959), Table 5-6. Secondary: FHWA HEC-22 (2009), Table 3-1.

### Material Database (embedded dict, not external file)

```python
MANNING_ROUGHNESS: dict[str, float] = {
    # Closed conduits
    "concrete":             0.013,
    "concrete_smooth":      0.012,
    "concrete_rough":       0.016,
    "corrugated_metal":     0.024,
    "corrugated_metal_paved_invert": 0.020,
    "hdpe":                 0.012,
    "hdpe_smooth":          0.011,
    "pvc":                  0.010,
    "cast_iron":            0.013,
    "ductile_iron":         0.013,
    "steel":                0.012,
    "steel_riveted":        0.017,
    "clay_tile":            0.014,
    "brick":                0.016,

    # Open channels — lined
    "concrete_trowel":      0.013,
    "concrete_float":       0.015,
    "asphalt_smooth":       0.013,
    "riprap":               0.035,
    "gabion":               0.028,

    # Open channels — unlined
    "earth_clean":          0.022,
    "earth_weedy":          0.030,
    "earth_gravelly":       0.025,
    "rock_cut":             0.035,
    "natural_clean":        0.030,
    "natural_weedy":        0.050,
    "natural_heavy_brush":  0.075,
    "floodplain_grass":     0.035,
    "floodplain_light_brush": 0.050,
    "floodplain_heavy_trees": 0.100,
}
```

### Key Function

```python
def resolve_roughness(roughness: float | str) -> float:
    """
    If float, return as-is. If str, lookup in MANNING_ROUGHNESS.
    Raises ValueError with list of valid names if not found.
    """
```

**Fuzzy matching:** If the exact key isn't found, suggest the closest match (e.g., `"concrte"` → `"Did you mean 'concrete'?"`). Use `difflib.get_close_matches`.

---

## Foundation Module 3: `geometry.py`

### Purpose

Compute cross-sectional properties (A, P, R, T, D_h) for all channel shapes. This is the mathematical foundation for Manning's equation, critical depth, and Froude number.

### Shapes and Their Geometry

All functions take depth `y` (in meters, SI) and shape parameters. All return SI values.

#### Trapezoidal (b = bottom width, z = side slope H:V)

```
A  = (b + z·y) · y
P  = b + 2·y·√(1 + z²)
T  = b + 2·z·y
R  = A / P
D_h = A / T
```

#### Rectangular (b = width) — special case: z = 0

```
A  = b · y
P  = b + 2·y
T  = b
R  = (b·y) / (b + 2·y)
D_h = y
```

#### Triangular (z = side slope on both sides)

```
A  = z · y²
P  = 2·y·√(1 + z²)
T  = 2·z·y
R  = z·y / (2·√(1 + z²))
D_h = y / 2
```

#### Circular (D = diameter) — uses central half-angle θ

```
r = D / 2
θ = arccos(1 - 2·y/D)        ← converts depth to angle

A  = r² · (θ - sin(θ)·cos(θ))
P  = 2·r·θ
T  = 2·r·sin(θ)
R  = A / P
D_h = A / T
```

**Edge cases for circular:**
- `y = 0` → `θ = 0`, all properties = 0. Guard with `y_min = 1e-10 * D`.
- `y = D` → `θ = π`, `T = 0`, `D_h → ∞`. Use full-pipe values directly: `A = π·r²`, `P = 2·π·r`, `R = D/4`.
- `y > D` → Surcharge condition. Raise `ValueError`.
- `y = D/2` → `θ = π/2` (half full). Useful sanity check: `A = π·r²/2`, `R = D/4` (same as full!).

**Critical numeric note for circular pipes:** Maximum flow capacity occurs at approximately `y/D ≈ 0.938` (`θ ≈ 2.748 rad`), NOT at full pipe. This is a well-known hydraulic phenomenon — flow actually decreases slightly between 93.8% full and 100% full due to the wetted perimeter increasing faster than the area.

### Implementation

```python
@dataclass(frozen=True, slots=True)
class SectionProperties:
    """Cross-sectional hydraulic properties."""
    area: float           # m²
    wetted_perimeter: float  # m
    hydraulic_radius: float  # m
    top_width: float      # m
    hydraulic_depth: float  # m  (A/T)

def trapezoidal(y: float, b: float, z: float) -> SectionProperties
def rectangular(y: float, b: float) -> SectionProperties
def triangular(y: float, z: float) -> SectionProperties
def circular(y: float, diameter: float) -> SectionProperties
```

Each function also has an `_unwrapped` version returning a plain tuple `(A, P, R)` for use in tight optimization loops:

```python
def _trap_apr(y: float, b: float, z: float) -> tuple[float, float, float]:
    """(area, wetted_perimeter, hydraulic_radius) — no object allocation."""
```

---

## Tier 1: `channels.py` — Open Channel Flow

### Classes

One class per channel shape, all sharing the same method interface:

```python
class TrapezoidalChannel:
    def __init__(self, bottom_width, side_slope, slope, roughness)
    def normal_flow(self, depth: float) -> float
    def normal_depth(self, flow: float) -> float
    def critical_depth(self, flow: float) -> float
    def froude_number(self, depth: float) -> float
    def flow_regime(self, depth: float) -> FlowRegime
    def full_flow_capacity(self) -> float  # only for CircularChannel

class RectangularChannel:   # same interface
class TriangularChannel:    # same interface
class CircularChannel:      # same interface + full_flow_capacity()
```

### Core Equation: Manning's

```
Q = (1/n) · A · R^(2/3) · S^(1/2)     [SI, always]
```

- `n` = Manning's roughness coefficient
- `A` = flow area (m²)
- `R` = hydraulic radius = A/P (m)
- `S` = bed slope (m/m, dimensionless)

The imperial form `Q = (1.49/n)·A·R^(2/3)·S^(1/2)` is NEVER used. The 1.49 factor is a unit conversion artifact that disappears when working in SI.

### Kernel Function

```python
def _manning_flow(n: float, area: float, R: float, S: float) -> float:
    """Manning's Q in m³/s. Pure SI. Zero overhead."""
    return (1.0 / n) * area * R ** (2 / 3) * S ** 0.5
```

### Normal Depth — Iterative Solution

**Algorithm:** `scipy.optimize.brentq` (Brent's method). Unconditionally convergent on a bracketed interval.

**Residual function:**
```
f(y) = (1/n) · A(y) · R(y)^(2/3) · S^(1/2) - Q_target = 0
```

**Bracketing strategy:**
- Lower: `y_lo = 1e-9` (near-zero depth, Q ≈ 0)
- Upper: start with initial estimate, double until `f(y_hi) > 0`:
  - For rectangular: `y_est = (n·Q / (S^0.5 · b))^(3/5)` (wide channel approx)
  - For others: start `y_hi = 1.0`, double up to `y_max = 100.0` (or D for circular)

**Convergence:** `xtol=1e-9`, `maxiter=100`

**Circular pipe special case:**
- Solve in θ-space: `θ ∈ (0, π)`, convert back via `y = r·(1 - cos(θ))`
- Check if Q exceeds max capacity (at θ ≈ 2.748 rad). If so, raise `SurchargeError`.

### Critical Depth — Iterative Solution

**Condition:** `Q²·T / (g·A³) = 1` (Froude number = 1)

**Closed-form solutions (use these, skip iteration):**
- Rectangular: `y_c = (Q² / (g·b²))^(1/3)`
- Triangular: `y_c = (2·Q² / (g·z²))^(1/5)`

**Iterative (trapezoidal, circular):**
```
f(y) = Q²·T(y) / (g·A(y)³) - 1 = 0
```
Solve with `brentq` on `[1e-9, y_upper]`. `f(y)` is monotonically decreasing for prismatic channels.

### Froude Number

```
Fr = Q / (A · √(g · D_h))

where D_h = A / T (hydraulic depth)
```

### FlowRegime Enum

```python
class FlowRegime(Enum):
    SUBCRITICAL = "subcritical"    # Fr < 1
    CRITICAL = "critical"          # Fr ≈ 1 (within tolerance)
    SUPERCRITICAL = "supercritical"  # Fr > 1
```

`flow_regime(depth)` computes Froude number and classifies. Critical tolerance: `|Fr - 1| < 0.01`.

### Reference Test Cases

**Test 1: Trapezoidal normal flow** (Chow 1959, Example 6-1)
```
b=20ft, z=1.5, S=0.0016, n=0.025, y=4ft
Expected: Q ≈ 519.5 cfs (14.71 m³/s)
```

**Test 2: Rectangular critical depth**
```
b=3m, Q=7 m³/s
Expected: y_c = (49/(9.81·9))^(1/3) = 0.822 m
Expected: Fr = 1.000
```

**Test 3: Circular pipe capacity**
```
D=0.6m, S=0.005, n=0.013 (concrete)
Full flow: A=0.2827 m², R=0.15m, Q_full = (1/0.013)·0.2827·0.15^(2/3)·0.005^0.5
Expected: Q_full ≈ 0.434 m³/s
Max Q at y/D≈0.938: Q_max ≈ 1.076 · Q_full ≈ 0.467 m³/s
```

**Test 4: Normal depth iteration** (verify round-trip)
```
For Test 1: Given Q=519.5 cfs, solve for y.
Expected: y ≈ 4.0 ft (must match input from Test 1)
```

---

## Tier 2: `hydrology.py` — Rainfall & Runoff

### SCS Curve Number Runoff

**Equation:**
```
S = 25400/CN - 254              [mm]
Ia = λ · S                      [λ = 0.2 standard]

If P ≤ Ia:  Q = 0
If P > Ia:  Q = (P - Ia)² / (P - Ia + S)
```

Where P = rainfall depth (mm), Q = runoff depth (mm).

**Edge cases:**
- CN = 100: S = 0, Ia = 0, Q = P (all rainfall becomes runoff)
- CN ≤ 0: invalid, raise ValueError
- CN > 100: invalid, raise ValueError
- P ≤ 0: Q = 0

**Incremental form for time series:**
Apply cumulatively, NOT per-increment:
```python
Q_cum[i] = scs_runoff(P_cum[i], CN)
Q_inc[i] = Q_cum[i] - Q_cum[i-1]
```

### Rational Method

```
Q = C · i · A / k

Imperial: Q[cfs]  = C · i[in/hr] · A[acres]           (k=1, approx)
Metric:   Q[m³/s] = C · i[mm/hr] · A[ha] / 360
```

**Implementation:** Accept C, i, A in user's unit system. Convert everything to SI internally, compute `Q = C · i_m_per_s · A_m2`, convert result back.

### Time of Concentration

Multiple methods — engineers compare them. All return Tc in minutes internally, converted to user's time preference.

**Kirpich (1940):**
```
Tc = 0.0078 · L^0.77 · S_pct^(-0.385)    [minutes]

L = flow path length (ft)
S_pct = slope in percent (rise/run × 100)
```

**NRCS Lag Method:**
```
Tc = L_lag / 0.6

L_lag = (L^0.8 · (S_ret + 1)^0.7) / (1140 · Y^0.5)    [hours]

L = flow path length (ft)
S_ret = (1000/CN) - 10
Y = average slope (%)
```

**FAA Method:**
```
Tc = 1.8 · (1.1 - C) · L^0.5 / (S_pct^(1/3))    [minutes]

C = rational method runoff coefficient
L = flow path length (ft)
S_pct = slope (%)
```

### SCS Dimensionless Unit Hydrograph

**Standard ordinates** (NEH Part 630, Chapter 16, Table 16-4):

```python
SCS_UH_ORDINATES: list[tuple[float, float]] = [
    # (t/Tp, q/qp)
    (0.0, 0.000), (0.1, 0.030), (0.2, 0.100), (0.3, 0.190),
    (0.4, 0.310), (0.5, 0.470), (0.6, 0.660), (0.7, 0.820),
    (0.8, 0.930), (0.9, 0.990), (1.0, 1.000), (1.1, 0.990),
    (1.2, 0.930), (1.3, 0.860), (1.4, 0.780), (1.5, 0.680),
    (1.6, 0.560), (1.7, 0.460), (1.8, 0.390), (1.9, 0.330),
    (2.0, 0.280), (2.2, 0.207), (2.4, 0.147), (2.6, 0.107),
    (2.8, 0.077), (3.0, 0.055), (3.2, 0.040), (3.4, 0.029),
    (3.6, 0.021), (3.8, 0.015), (4.0, 0.011), (4.5, 0.005),
    (5.0, 0.000),
]
```

**Scaling:**
```
Tp = Δt/2 + 0.6·Tc        [hours]
qp = 0.208 · A · Q_depth / Tp    [m³/s, A in km², Q_depth in mm, Tp in hours]

(Imperial: qp = 484 · A · Q_depth / Tp  [cfs, A in mi², Q_depth in inches, Tp in hours])
```

**Constructing the unit hydrograph:**
1. Interpolate SCS_UH_ORDINATES to the computation time step Δt
2. Scale: `UH(t) = qp · (q/qp interpolated at t/Tp)`
3. The UH represents flow response to 1 unit of runoff depth

**Composite hydrograph via convolution:**
```python
composite = np.convolve(runoff_increments, unit_hydrograph_ordinates)
```

`np.convolve` is the correct tool — this is a linear discrete convolution.

### DesignStorm Class

```python
class DesignStorm:
    """A rainfall hyetograph (intensity vs. time)."""

    @classmethod
    def from_table(cls, durations, depths, units="mm") -> "DesignStorm"

    @classmethod
    def from_idf(cls, location, return_period, duration, method="SCS_Type_II") -> "DesignStorm"

    def intensity_at(self, duration) -> float   # mm/hr (or in/hr)
    def depth_at(self, duration) -> float        # cumulative depth
    def hyetograph(self, timestep) -> np.ndarray  # incremental depths per timestep

    def plot(self) -> matplotlib.figure.Figure
```

**SCS Type II distribution** — the most common in the US. Standard cumulative fractions of 24-hour rainfall:

```python
SCS_TYPE_II: list[tuple[float, float]] = [
    # (fraction of 24h, cumulative fraction of total depth)
    (0.000, 0.000), (0.042, 0.011), (0.083, 0.022),
    (0.125, 0.035), (0.167, 0.048), (0.208, 0.063),
    (0.250, 0.080), (0.292, 0.098), (0.333, 0.120),
    (0.375, 0.147), (0.396, 0.163), (0.417, 0.181),
    (0.438, 0.204), (0.458, 0.235), (0.479, 0.283),
    (0.487, 0.357), (0.492, 0.663), (0.500, 0.735),
    (0.521, 0.772), (0.542, 0.799), (0.563, 0.820),
    (0.583, 0.838), (0.625, 0.866), (0.667, 0.891),
    (0.708, 0.914), (0.750, 0.935), (0.792, 0.953),
    (0.833, 0.968), (0.875, 0.980), (0.917, 0.989),
    (0.958, 0.995), (1.000, 1.000),
]
```

**`from_idf` with `location` string:** This is a stretch goal for Phase 1. Initially, only `from_table()` is required. NOAA Atlas 14 API integration can be added later.

### Watershed Dataclass

```python
@dataclass
class Watershed:
    area: float              # converted to km² internally
    curve_number: float      # 1-99
    time_of_concentration: float  # converted to seconds internally
    slope: float = 0.0       # m/m, optional
```

### Reference Test Cases

**Test 1: SCS Runoff** (NEH Chapter 10)
```
P=5.0 in (127 mm), CN=75
S = 25400/75 - 254 = 84.67 mm
Ia = 0.2 · 84.67 = 16.93 mm
Q = (127 - 16.93)² / (127 - 16.93 + 84.67) = 12113.1/194.74 = 62.2 mm (2.45 in)
```

**Test 2: Rational Method**
```
C=0.70, i=88.9 mm/hr, A=6.07 ha
Q = 0.70 · 88.9 · 6.07 / 360 = 1.049 m³/s
```

**Test 3: Kirpich Tc**
```
L=3000 ft, S=2%
Tc = 0.0078 · 3000^0.77 · 2^(-0.385) = 0.0078 · 446.3 · 0.765 = 26.6 min
```

---

## Tier 3: `structures.py` — Hydraulic Structures

### Orifice

```
Q = Cd · A · √(2·g·H)

Cd = discharge coefficient (default 0.61 for sharp-edged)
A  = orifice area (m²)
H  = effective head above orifice centroid (m)
g  = 9.80665 m/s²

When H ≤ 0: Q = 0
```

```python
class Orifice:
    def __init__(self, diameter, invert=0.0, Cd=0.61)
    def discharge(self, stage: float) -> float
    def __add__(self, other: "Weir") -> "CompositeOutlet"
```

### Weir — Rectangular (Sharp-Crested)

```
Q = Cw · L · H^(3/2)

Cw = 1.84  [SI: m^(1/2)/s]    (= 3.33 in imperial ft units)
L  = weir length (m)
H  = head above crest (m)

When H ≤ 0: Q = 0
```

### Weir — V-Notch

```
Q = (8/15) · Cd · tan(θ/2) · √(2·g) · H^(5/2)

Cd = 0.58-0.61 (sharp-edged, angle-dependent)
θ  = notch angle (radians)
H  = head above notch vertex (m)

For 90° notch (θ = π/2):
Q = 1.38 · H^(2.5)    [SI]
```

### Weir — Broad-Crested

```
Q = Cw · L · H^(3/2)

Cw = 1.70  [SI, typical value]
```

### CompositeOutlet

When orifices and weirs act simultaneously:
```
Q_total(h) = Q_orifice(h) + Q_weir(h) + ...
```

```python
class CompositeOutlet:
    """Sum of multiple outlet structures."""
    def __init__(self, *structures)
    def discharge(self, stage: float) -> float:
        return sum(s.discharge(stage) for s in self.structures)

    def stage_discharge_curve(self, stages: np.ndarray) -> np.ndarray
```

The `+` operator between Orifice and Weir returns a CompositeOutlet:
```python
outlet = Orifice(diameter=0.3) + Weir(length=3.0, crest=1.5)
```

### Culvert (FHWA HDS-5 Methodology)

**Always computes BOTH inlet and outlet control, reports the governing one.**

**Inlet control — unsubmerged (Form 1):**
```
HW/D = K · (Q / (A·D^0.5))^M + ks·S
```

**Inlet control — submerged (Form 2):**
```
HW/D = c · (Q / (A·D^0.5))² + Y - 0.5·S
```

Transition at approximately `Q/(A·D^0.5) ≈ 3.5`

**Inlet coefficients** (FHWA HDS-5 Table B-1, circular concrete):

| Inlet Type     | K      | M   | c      | Y    |
|---------------|--------|-----|--------|------|
| `square_edge` | 0.0098 | 2.0 | 0.0398 | 0.67 |
| `groove_end`  | 0.0018 | 2.0 | 0.0292 | 0.74 |
| `beveled`     | 0.0045 | 2.0 | 0.0317 | 0.69 |

**Outlet control:**
```
HW_oc = TW + (1 + ke + kf)·V²/(2g) - S·L

ke = entrance loss coefficient:
    square_edge: 0.5
    groove_end:  0.2
    beveled:     0.25
    projecting:  0.9

kf = friction factor = 29·n²·L / R^(4/3)   [imperial]
   = 19.63·n²·L / R^(4/3)                  [SI]
```

**Governing condition:** `HW = max(HW_inlet, HW_outlet)`

```python
class Culvert:
    def __init__(self, shape, diameter, length, slope, material, inlet)
    def analyze(self, headwater=None, tailwater=0.0, flow=None) -> CulvertResult
    def performance_curve(self, hw_range, steps=50) -> PerformanceCurve
```

**`CulvertResult` dataclass:**
```python
@dataclass
class CulvertResult:
    flow: float
    headwater: float
    control: Literal["INLET_CONTROL", "OUTLET_CONTROL"]
    headwater_ratio: float  # HW/D
    velocity: float
```

### Reference Test Cases

**Test 1: Orifice**
```
D=0.3m, Cd=0.61, head=2.0m
A = π·0.3²/4 = 0.0707 m²
Q = 0.61 · 0.0707 · √(2·9.81·2.0) = 0.0431 · 6.264 = 0.270 m³/s
```

**Test 2: Rectangular weir**
```
L=3.0m, H=0.5m, Cw=1.84
Q = 1.84 · 3.0 · 0.5^1.5 = 5.52 · 0.3536 = 1.952 m³/s
```

**Test 3: Culvert** (FHWA HDS-5 Example)
```
D=3ft, L=100ft, n=0.012, S=0.02, inlet=square_edge, Q=110cfs, TW=2.5ft
Expected: HW_inlet ≈ 11.6 ft, HW_outlet ≈ 8.0 ft → INLET_CONTROL
HW/D ≈ 3.87
```

---

## Tier 3: `routing.py` — Detention Pond Routing

### Modified Puls (Storage-Indication) Method

**Core equation** (mass balance, rearranged):
```
SI(h₂) = I₁ + I₂ + [SI(h₁) - 2·O(h₁)]

where SI(h) = 2·S(h)/Δt + O(h)
```

**This is NOT iterative within each time step** when using the SI formulation. The implicit solve that causes Excel pain is eliminated. Each step is a direct table lookup.

### Algorithm

1. **Pre-compute** stage-discharge `O(h)` from the outlet structure(s)
2. **Pre-compute** storage-indication table: `SI(h) = 2·S(h)/Δt + O(h)`
3. **Route:** at each time step, compute RHS, interpolate `SI⁻¹` to find h₂

```python
class DetentionPond:
    def __init__(self, stage_storage, outlet)
    def route(self, inflow) -> RoutingResult

@dataclass
class RoutingResult:
    outflow: np.ndarray       # time series
    stages: np.ndarray        # time series
    peak_inflow: float
    peak_outflow: float
    peak_reduction: float     # fraction (e.g., 0.62 = 62%)
    max_stage: float
    time_to_peak: float
```

**`stage_storage`** — accepts either:
- A dict `{stage: storage}` (user-friendly)
- A 2D array of `(stage, storage)` pairs

**Time step selection:** `Δt` is inferred from the inflow hydrograph (assumed uniform spacing). If the inflow is a Hydrograph object from `hydrology.py`, Δt comes from its metadata.

**Edge cases:**
- Inflow = 0 at all times → outflow = 0, stage = initial stage
- Pond overflow (stage exceeds max in table) → extrapolate linearly with warning, or raise `PondOverflowError`
- Negative outflow (shouldn't happen physically) → clamp to 0

### Reference Test Case

```
Stage-storage: {0: 0, 1: 10000, 2: 25000, 3: 45000} m : m³
Outlet: Weir(L=2, crest=1.0, Cw=1.84)
Δt = 3600s (1 hour)

SI table:
  h=0: SI = 0 + 0 = 0
  h=1: SI = 2·10000/3600 + 0 = 5.556
  h=2: SI = 2·25000/3600 + 3.680 = 17.57
  h=3: SI = 2·45000/3600 + 10.40 = 35.40

Inflow: triangular, peak=15 m³/s at t=3h, duration=8h
Expected: peak reduction 40-60% depending on pond size relative to inflow volume
```

---

## Tier 4: `pressure.py` — Pressurized Pipe Flow

### Darcy-Weisbach

```
h_f = f · (L/D) · (V²/2g)

f = friction factor (from Moody diagram / Colebrook-White)
L = pipe length (m)
D = pipe diameter (m)
V = flow velocity (m/s)
g = 9.80665 m/s²

Colebrook-White (implicit, solve iteratively):
1/√f = -2·log₁₀(ε/(3.7·D) + 2.51/(Re·√f))

Re = V·D/ν (Reynolds number)
ε = absolute roughness (m)
ν = kinematic viscosity (m²/s, default 1.004e-6 for water at 20°C)
```

**Explicit approximation** (Swamee-Jain 1976, error < 1% for 10⁻⁶ < ε/D < 10⁻² and 5000 < Re < 10⁸):
```
f = 0.25 / [log₁₀(ε/(3.7·D) + 5.74/Re^0.9)]²
```

Use Swamee-Jain as initial guess, then 2-3 iterations of Colebrook-White for precision.

### Hazen-Williams

```
V = k · C · R^0.63 · S^0.54

k = 0.8492  [SI]  (or 1.318 imperial)
C = Hazen-Williams coefficient (dimensionless, e.g., 150 for PVC)
R = hydraulic radius (m)
S = friction slope = h_f / L

Or in head loss form for a pipe:
h_f = (10.67 · Q^1.852 · L) / (C^1.852 · D^4.87)    [SI]
```

### Minor Losses

```
h_m = K · V²/(2g)

K values (standard):
    entrance_sharp:    0.5
    entrance_rounded:  0.2
    exit:              1.0
    90_elbow:          0.9
    45_elbow:          0.4
    tee_through:       0.6
    tee_branch:        1.8
    gate_valve_open:   0.2
    check_valve:       2.5
    butterfly_valve:   0.3
```

### Hydraulic Jump

**Sequent depth** (Belanger equation, rectangular channel):
```
y₂/y₁ = 0.5 · (√(1 + 8·Fr₁²) - 1)

Energy loss:
ΔE = (y₂ - y₁)³ / (4·y₁·y₂)
```

### Reference Test Cases

**Test 1: Darcy-Weisbach**
```
L=100m, D=0.3m, Q=0.05 m³/s, ε=0.045mm (commercial steel), ν=1.004e-6
V = Q/A = 0.05/0.0707 = 0.707 m/s
Re = 0.707·0.3/1.004e-6 = 211,255
f ≈ 0.0186 (from Colebrook-White)
hf = 0.0186·(100/0.3)·(0.707²/(2·9.81)) = 0.158 m
```

**Test 2: Hazen-Williams**
```
L=100m, D=0.3m, Q=0.05 m³/s, C=130 (cast iron)
hf = 10.67 · 0.05^1.852 · 100 / (130^1.852 · 0.3^4.87)
   = 10.67 · 0.00308 · 100 / (8375 · 0.002025)
   = 3.287 / 16.96 = 0.194 m
```

**Test 3: Hydraulic jump**
```
y₁=0.3m, Fr₁=3.0 (supercritical), rectangular channel
y₂ = 0.3 · 0.5 · (√(1+8·9) - 1) = 0.3 · 0.5 · (√73 - 1) = 0.3 · 3.772 = 1.132 m
ΔE = (1.132-0.3)³/(4·0.3·1.132) = 0.575/1.359 = 0.423 m
```

---

## Build Order (Implementation Sequence)

Each step can be tested independently before moving to the next.

```
Step 1:  units.py              ← everything depends on this
Step 2:  materials.py          ← simple dict lookup, resolve_roughness()
Step 3:  _types.py             ← FlowRegime enum, shared dataclasses
Step 4:  geometry.py           ← test against known A/P/R values
Step 5:  channels.py           ← test against Chow reference values
Step 6:  hydrology.py (SCS)    ← test against NEH examples
Step 7:  hydrology.py (Rational, Tc) ← simpler calculations
Step 8:  structures.py (Orifice, Weir) ← needed before routing
Step 9:  routing.py            ← test with known stage-storage-discharge
Step 10: structures.py (Culvert) ← most complex, saved for last in Tier 3
Step 11: pressure.py           ← independent, can be parallel with 8-10
Step 12: __init__.py           ← public re-exports, final integration test
```

---

## Dependencies

**Required (core):**
- `numpy >= 1.24`
- `scipy >= 1.10` (for `brentq`, `interp1d`)

**Optional (visualization):**
- `matplotlib >= 3.6` (for `.plot()` methods)

**Dev:**
- `pytest`
- `ruff`
- `mypy`

That's it. Zero heavy dependencies. `pip install hydroflow` will be fast and painless.
