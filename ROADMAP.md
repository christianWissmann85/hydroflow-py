# HydroFlow Roadmap

> **Mission:** Build the Python library that replaces Excel spreadsheets and $20k/year proprietary software for practicing water engineers — with an AI-native API from day one.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 4: REPORTING                           │
│         PDF / HTML / Markdown — "One-Click" Deliverables        │
├─────────────────────────────────────────────────────────────────┤
│                LAYER 3: AI & OPTIMIZATION                       │
│     Parameter Sweeps · Calibration · JSON Schemas · LLM-Ready   │
├─────────────────────────────────────────────────────────────────┤
│                LAYER 2: WORKFLOWS & COUPLING                    │
│        Model Chaining · Rain→Drainage→River Pipelines           │
├─────────────────────────────────────────────────────────────────┤
│                LAYER 1: SOLVER WRAPPERS                         │
│     EPANET (pipes) · SWMM (drainage) · MODFLOW (groundwater)    │
├─────────────────────────────────────────────────────────────────┤
│              LAYER 0: CORE CALCULATIONS                         │
│   Manning's · Rational Method · SCS · Culverts · Pond Routing   │
├─────────────────────────────────────────────────────────────────┤
│                    FOUNDATION                                   │
│        Units · Materials DB · Channel Geometry · Utilities      │
└─────────────────────────────────────────────────────────────────┘
```

Each layer builds on the ones below it, but every layer is independently useful.

---

## Phase 1: Foundation + Layer 0 MVP — "The Excel Killer"

**Goal:** A pip-installable library that replaces the most common hydraulic engineering Excel spreadsheets. If we ship nothing else, this alone fills a gap that thousands of engineers need.

### 1.1 Foundation (Build First)

The cross-cutting infrastructure that every layer depends on.

| Module | Description | Priority |
|--------|-------------|:--------:|
| `hydroflow.units` | Unit system (metric/imperial) with transparent conversion. Engineers in the US use feet/cfs/acres; everyone else uses metric. Must be seamless, never surprising. | P0 |
| `hydroflow.materials` | Lookup database for roughness coefficients, pipe materials, soil properties. Engineers should type `"concrete"` not `n=0.013`. Stored as embedded data (JSON/TOML), zero external dependencies. | P0 |
| `hydroflow.geometry` | Channel cross-section geometry engine — area, wetted perimeter, hydraulic radius, top width for: trapezoidal, rectangular, circular, triangular, and custom shapes. This is the mathematical foundation for all open-channel calculations. | P0 |

### 1.2 Layer 0: Core Calculations

Ordered by priority — build top-to-bottom.

#### Tier 1: Open Channel Flow (Build First)

These are the most fundamental calculations in hydraulic engineering. Every other module builds on these.

| Function / Class | What It Does | Engineering Context |
|-----------------|--------------|-------------------|
| `TrapezoidalChannel` | Manning's equation for trapezoidal channels | Roadside ditches, irrigation canals |
| `RectangularChannel` | Manning's equation for rectangular channels | Concrete-lined channels, box culverts |
| `CircularChannel` | Manning's equation for partially-full circular pipes | Storm sewers, sanitary sewers |
| `TriangularChannel` | Manning's equation for V-shaped channels | Roadside gutters, small swales |
| `.normal_depth()` | Iterative solve for depth given flow | "How deep will the water be?" |
| `.normal_flow()` | Direct solve for flow given depth | "How much can this channel carry?" |
| `.critical_depth()` | Solve for critical depth | Flow regime transitions |
| `.flow_regime()` | Froude number + subcritical/critical/supercritical classification | Every hydraulic design check |
| `.full_flow_capacity()` | Max capacity of a closed conduit (circular) | "Will this pipe handle the storm?" |

**Acceptance criteria:** An engineer can size a drainage channel in 5 lines of Python, with correct results matching published reference tables (e.g., Chow's Open-Channel Hydraulics).

#### Tier 2: Hydrology — Rainfall & Runoff

| Function / Class | What It Does | Engineering Context |
|-----------------|--------------|-------------------|
| `DesignStorm` | Construct a design storm hyetograph from IDF data | "What rainfall do I design for?" |
| `DesignStorm.from_table()` | Build storm from manual IDF table input | When you have local data |
| `time_of_concentration()` | Compute Tc using Kirpich, FAA, NRCS Lag, or Kerby-Kirpich methods | Critical parameter for all runoff calcs |
| `rational_method()` | Peak flow from the Rational Method (Q = CiA) | Small catchments (<80 ha), the most-used formula in civil engineering |
| `Watershed` | Container for watershed properties (area, CN, Tc, slope) | Reusable across methods |
| `scs_unit_hydrograph()` | SCS dimensionless unit hydrograph method | Medium catchments, standard practice |
| `scs_curve_number_runoff()` | SCS CN method for runoff depth from rainfall depth | Pairs with unit hydrograph |

**Acceptance criteria:** Reproduce the SCS TR-55 example problems exactly. An engineer can go from rainfall data to a runoff hydrograph in <10 lines.

#### Tier 3: Hydraulic Structures

| Function / Class | What It Does | Engineering Context |
|-----------------|--------------|-------------------|
| `Culvert` | Full culvert analysis: inlet control, outlet control, auto-selects governing | Road crossings — designed daily |
| `.performance_curve()` | Headwater vs. discharge relationship | Standard deliverable for culvert design |
| `Orifice` | Orifice equation (sharp-edged, submerged, free) | Pond outlet structures |
| `Weir` | Sharp-crested, broad-crested, V-notch, Cipolletti weirs | Pond outlets, flow measurement |
| `DetentionPond` | Stage-storage-discharge + Modified Puls routing | Required for every land development project |
| `.route()` | Inflow hydrograph → outflow hydrograph via Modified Puls | The core detention calculation |

**Acceptance criteria:** Detention pond routing matches hand-calculated Modified Puls results. The `Orifice + Weir` outlet combination produces correct composite stage-discharge curves.

#### Tier 4: Pipe Sizing & Energy

| Function / Class | What It Does | Engineering Context |
|-----------------|--------------|-------------------|
| `darcy_weisbach()` | Head loss in pressurized pipes | Pressure system design |
| `hazen_williams()` | Empirical head loss (common in US water distribution) | Municipal pipe sizing |
| `minor_losses()` | Head loss from fittings, bends, valves | Detailed pipe system design |
| `energy_equation()` | Bernoulli's equation between two points | General hydraulic analysis |
| `momentum_equation()` | Momentum balance for hydraulic jumps, forces on bends | Structural design of channels |
| `hydraulic_jump()` | Sequent depth, energy loss, jump location | Channel design downstream of structures |

**Acceptance criteria:** Darcy-Weisbach and Hazen-Williams match standard reference calculations. Hydraulic jump sequent depths match Belanger equation.

### Phase 1 Deliverables

- [ ] `pip install hydroflow` works (published to PyPI)
- [ ] All Tier 1-4 functions implemented with tests
- [ ] Every function has a docstring with an engineering example
- [ ] README with "Getting Started" showing a real engineering workflow
- [ ] Unit conversion works transparently (metric/imperial)
- [ ] Material/roughness lookup works for common materials
- [ ] Test coverage >90% for all calculation modules
- [ ] CI pipeline (GitHub Actions): tests + linting + type checking

---

## Phase 2: Layer 1a — EPANET Wrapper (Pipe Networks)

**Goal:** Build a clean, engineer-friendly API over EPANET for water distribution network analysis. Use WNTR or epanet-python as the backend engine — we don't rewrite the solver, we build a better cockpit.

### Why EPANET First

- Most mature open-source solver (US EPA, 30+ years)
- Simplest input/output format of the three solvers
- WNTR exists as a Python backend (we wrap it, not replace it)
- Water distribution is a universal need

### Key Modules

| Module | Description |
|--------|-------------|
| `hydroflow.network.WaterNetwork` | The main model class. Add junctions, reservoirs, tanks, pipes, pumps, valves using clean methods. |
| `hydroflow.network.components` | Component classes (Junction, Pipe, Pump, Tank, etc.) with sensible defaults, validation, and material auto-lookup. |
| `hydroflow.network.rules` | Human-readable control rule DSL. `"tank.level < 3 AND time.hour >= 22"` instead of 6 lines of object composition. |
| `hydroflow.network.simulate` | Simulation runner. Immutable — never mutates the model. Returns a `NetworkResults` DataFrame container. |
| `hydroflow.network.results` | `NetworkResults` class: `.pressures`, `.flows`, `.velocities` as DataFrames. `.health_check()` for instant diagnostics. |
| `hydroflow.network.io` | Import/export: `.inp` files, GeoJSON, CSV. Interop with existing EPANET models. |
| `hydroflow.network.errors` | Error translation layer. Maps EPANET error codes to human-readable messages with fix suggestions. |

### Key Design Decisions

- **Backend:** WNTR's `EpanetSimulator` for speed, with option to use `WNTRSimulator` for pressure-dependent demand.
- **Immutability:** `simulate()` never mutates the model. No more pickle hacks for parameter sweeps.
- **Time handling:** `"24h"`, `"15min"`, `"7 days"` — never raw seconds.
- **Validation:** Errors at construction time, not at simulation time. If you add a pipe to a nonexistent node, it fails immediately with a clear message.

### Phase 2 Deliverables

- [ ] Create, simulate, and analyze pipe networks from scratch in Python
- [ ] Import existing `.inp` files and enhance them
- [ ] Health check identifies common design issues automatically
- [ ] Error messages explain problems and suggest fixes
- [ ] Results as labeled DataFrames with time-axis
- [ ] Network visualization (matplotlib, basic but functional)
- [ ] At least 3 tutorial notebooks (simple network, tank filling, pump scheduling)

---

## Phase 3: Layer 3 + Layer 1b — Optimization & SWMM

**Goal:** Add optimization/calibration capabilities AND the SWMM (stormwater) wrapper. These are paired because stormwater design is inherently an optimization problem ("what pipe sizes minimize cost while preventing flooding?").

### Layer 3: AI & Optimization

| Module | Description |
|--------|-------------|
| `hydroflow.optimize.sweep` | `ParameterSweep` — run a model across a range of parameter values, parallel by default. |
| `hydroflow.optimize.minimize` | `minimize_cost()` — find optimal design variables subject to engineering constraints. Wraps scipy.optimize with engineering-aware objective functions. |
| `hydroflow.optimize.calibrate` | `calibrate()` — match model to observed data. Supports RMSE, NSE, PBIAS metrics. Multiple algorithms (differential evolution, Nelder-Mead, basin-hopping). |
| `hydroflow.optimize.sensitivity` | Sensitivity analysis — which parameters matter most? Morris method, Sobol indices (via SALib). |
| `hydroflow.schema` | JSON schema export for any model. Enables LLM agents to read model structure, understand parameter ranges, and generate valid modifications. |

### Layer 1b: SWMM Wrapper (Stormwater)

| Module | Description |
|--------|-------------|
| `hydroflow.stormwater.StormwaterModel` | Main model class for urban drainage. Add subcatchments, conduits, junctions, outfalls. |
| `hydroflow.stormwater.components` | Subcatchment (with `land_use` auto-defaults), Conduit (circular, box, custom shapes), Junction, Outfall, Storage. |
| `hydroflow.stormwater.simulate` | Simulation runner. Integrates with Layer 0's `DesignStorm`. |
| `hydroflow.stormwater.results` | `StormwaterResults`: peak flows, flooding volumes, max depths, time to peak — the numbers engineers actually need. |
| `hydroflow.stormwater.io` | Import/export `.inp` files. Interop with existing SWMM models. |

### Phase 3 Deliverables

- [ ] Parameter sweeps run in parallel out of the box
- [ ] Cost optimization for pipe networks with real pipe catalogs
- [ ] Calibration framework with multiple metrics and algorithms
- [ ] JSON schema export for AI/LLM integration
- [ ] Create and simulate stormwater models from scratch
- [ ] Import existing SWMM `.inp` files
- [ ] Integration: Layer 0 `DesignStorm` feeds directly into SWMM models

---

## Phase 4: Layer 2 + Layer 1c — Workflows & MODFLOW

**Goal:** The "glue layer" that chains models together, plus the groundwater wrapper.

### Layer 2: Workflows & Coupling

| Module | Description |
|--------|-------------|
| `hydroflow.workflow.Workflow` | Pipeline definition: named steps with explicit data connections. |
| `hydroflow.workflow.adapters` | Data adapters between models: time-step interpolation, spatial mapping, unit conversion at boundaries. |
| `hydroflow.workflow.compare` | `compare()` — pre-development vs. post-development analysis with automatic summary statistics. |

### Layer 1c: MODFLOW Wrapper (Groundwater)

| Module | Description |
|--------|-------------|
| `hydroflow.groundwater.GroundwaterModel` | Main model class. Define grid, layers (by name!), boundary conditions. |
| `hydroflow.groundwater.layers` | Layer definition using hydrogeological terms: `"unconfined"`, `"confined"`, hydraulic conductivity `K` — not `icelltype`, `npf`, `k33`. |
| `hydroflow.groundwater.boundaries` | Rivers, wells, recharge, drains, constant head — named and intuitive. |
| `hydroflow.groundwater.results` | `GroundwaterResults`: head maps, drawdown, water budgets. |

### Phase 4 Deliverables

- [ ] Chain: DesignStorm → StormwaterModel → RiverModel in one script
- [ ] Pre/post development comparison with automatic statistics
- [ ] Groundwater models defined with hydrogeological vocabulary
- [ ] Results include water budgets, drawdown maps, head time series
- [ ] At least 1 end-to-end tutorial: full site development analysis

---

## Phase 5: Layer 4 — Reporting & Polish

**Goal:** The "proprietary killer feature." One-script report generation that produces what clients actually receive.

### Layer 4: Reporting

| Module | Description |
|--------|-------------|
| `hydroflow.report.Report` | Build a structured report: sections, figures, tables, narrative text. |
| `hydroflow.report.export` | Export to PDF (via weasyprint or similar), HTML (standalone), Markdown (for Git). |
| `hydroflow.report.templates` | Pre-built templates for common deliverables: drainage analysis, culvert design, detention pond sizing. |

### Polish & Ecosystem

| Task | Description |
|------|-------------|
| **Documentation site** | Sphinx/MkDocs site with tutorials, API reference, engineering background. |
| **Cookbook** | Recipe-style examples: "How to size a culvert", "How to design a detention pond", "How to optimize a pipe network". |
| **QGIS plugin** | Optional: read/write hydroflow models from QGIS (stretch goal). |
| **Web dashboard** | Optional: Streamlit/Panel app for non-coders (stretch goal). |

### Phase 5 Deliverables

- [ ] Generate PDF reports from any analysis
- [ ] At least 3 report templates (drainage, culvert, detention)
- [ ] Full documentation site live
- [ ] Cookbook with 10+ real-world examples
- [ ] v1.0 release 🎉

---

## Cross-Cutting Principles (All Phases)

### API Design

- **Mirror the engineer's mental model, not the solver's.** A hydrogeologist thinks "layer of clay with K=0.01" not `ModflowGwfnpf(icelltype=[0])`.
- **Progressive disclosure.** Simple things are simple (`channel.normal_depth(flow=5)`). Complex things are possible but don't clutter the basic API.
- **Sensible defaults everywhere.** `land_use="commercial"` auto-sets infiltration, roughness, and depression storage. The user can override any default.
- **Fail early, fail clearly.** Validation at construction time, not simulation time. Error messages explain what went wrong AND what to do about it.
- **Human-readable time.** `"24h"`, `"15min"`, `"3 days"` — never raw seconds or Fortran stress period indices.

### Code Quality

- **Type hints everywhere** (mypy strict). An LLM reading our code should understand every function signature without guessing.
- **Tests for every calculation** against published reference values (textbook problems, government manuals).
- **Zero required dependencies beyond numpy/scipy** for Layer 0. Solver backends (WNTR, PySWMM, FloPy) are optional extras: `pip install hydroflow[epanet]`.
- **Linting with ruff**, formatting consistent, no dead code.

### Documentation

- Every public function gets a docstring with:
  - What it computes (one sentence)
  - Parameters with units
  - A minimal example
  - A reference (textbook, manual, or standard)
- Engineering background sections explain the theory for non-specialists.

---

## Dependencies Strategy

```
hydroflow (core)          → numpy, scipy (only)
hydroflow[epanet]         → + wntr
hydroflow[swmm]           → + pyswmm
hydroflow[groundwater]    → + flopy
hydroflow[optimize]       → + scipy (already included), SALib (optional)
hydroflow[report]         → + weasyprint or fpdf2, jinja2
hydroflow[all]            → everything
```

Layer 0 works with ZERO heavy dependencies. This is critical — "dependency hell" is the #1 complaint about Python hydrology tools.

---

## Definition of Done: v1.0

HydroFlow v1.0 is ready when an engineer can:

1. **Size a drainage channel** using Manning's equation → Layer 0
2. **Generate a runoff hydrograph** from a design storm → Layer 0
3. **Design a detention pond** with Modified Puls routing → Layer 0
4. **Analyze a pipe network** for pressure and velocity → Layer 1
5. **Optimize pipe diameters** for minimum cost → Layer 3
6. **Chain rainfall → drainage → analysis** in one script → Layer 2
7. **Generate a PDF report** of the entire analysis → Layer 4

...all without opening Excel, a GUI, or spending a dollar on software.
