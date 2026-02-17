# HydroFlow

**The Python library for water engineering — from Excel to elegant code.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy%20strict-blue.svg)](https://mypy-lang.org/)
[![Code Style: ruff](https://img.shields.io/badge/code%20style-ruff-purple.svg)](https://docs.astral.sh/ruff/)

HydroFlow replaces the Excel spreadsheets and $20k/year proprietary software that water engineers depend on daily. Manning's equation, SCS hydrology, culvert sizing, detention pond routing — all in clean, tested, AI-friendly Python.

## Quick Start

```bash
pip install hydroflow
```

```python
import hydroflow as hf

# Size a drainage channel in 4 lines
channel = hf.TrapezoidalChannel(
    bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="concrete"
)

print(channel.normal_flow(depth=1.5))      # 20.81 m³/s
print(channel.normal_depth(flow=20.81))    # 1.50 m
print(channel.flow_regime(depth=1.5))      # FlowRegime.SUBCRITICAL
```

No memorizing coefficients. Type `"concrete"` instead of `n=0.013`.

## Works in Imperial Too

```python
hf.set_units("imperial")

channel = hf.TrapezoidalChannel(
    bottom_width=20, side_slope=1.5, slope=0.0016, roughness=0.025
)

print(channel.normal_flow(depth=4.0))  # 516.7 cfs
```

All internal math uses SI. The imperial constant 1.49 never appears in the codebase — an entire class of bugs, eliminated.

## Channel Shapes

```python
# Trapezoidal — roadside ditches, irrigation canals
hf.TrapezoidalChannel(bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="earth_clean")

# Rectangular — concrete-lined channels
hf.RectangularChannel(width=5.0, slope=0.002, roughness="concrete")

# Triangular — roadside gutters, small swales
hf.TriangularChannel(side_slope=3.0, slope=0.01, roughness="earth_gravelly")

# Circular — storm sewers, sanitary sewers
pipe = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="pvc")
pipe.full_flow_capacity()   # 0.514 m³/s
pipe.max_flow_capacity()    # 0.551 m³/s (at y/D ≈ 0.938, not at full!)
```

Every channel computes:
- **`normal_flow(depth)`** — discharge at a given depth (Manning's equation)
- **`normal_depth(flow)`** — iterative solve for depth at a given discharge
- **`critical_depth(flow)`** — depth where Froude number = 1
- **`froude_number(depth)`** — dimensionless flow regime indicator
- **`flow_regime(depth)`** — `SUBCRITICAL`, `CRITICAL`, or `SUPERCRITICAL`

## Designed for Optimization

Every channel exposes its SI parameters for zero-overhead inner loops:

```python
from hydroflow.channels import _manning_flow
from hydroflow.geometry import _trap_apr
from scipy.optimize import minimize_scalar

channel = hf.TrapezoidalChannel(
    bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="concrete"
)
b, z, S, n = channel.si_params  # extract once, use millions of times

def cost(depth):
    A, P, R = _trap_apr(depth, b, z)
    Q = _manning_flow(n, A, R, S)
    return (Q - 15.0) ** 2  # target 15 m³/s

result = minimize_scalar(cost, bounds=(0.01, 10.0), method="bounded")
print(f"Optimal depth: {result.x:.3f} m")  # finds it in milliseconds
```

The public API handles units. The kernel functions are pure math — fast enough for Monte Carlo, calibration, and AI agents.

## Material Lookup

No more memorizing roughness coefficients:

```python
hf.resolve_roughness("concrete")        # 0.013
hf.resolve_roughness("pvc")             # 0.010
hf.resolve_roughness("corrugated_metal") # 0.024
hf.resolve_roughness("earth_clean")     # 0.022

# Typo? We'll help.
hf.resolve_roughness("concrte")
# ValueError: Unknown material 'concrte'. Did you mean: 'concrete', 'concrete_smooth', 'concrete_rough'?
```

30+ materials from Chow (1959) and FHWA HEC-22 built in.

## Explicit Units When You Need Them

```python
# Global setting
hf.set_units("imperial")
channel = hf.TrapezoidalChannel(bottom_width=10, ...)  # feet

# Or tag individual values — overrides global setting
channel = hf.TrapezoidalChannel(bottom_width=hf.ft(10), ...)  # feet, even in metric mode
channel = hf.TrapezoidalChannel(bottom_width=hf.m(3), ...)    # meters, even in imperial mode
```

## Roadmap

HydroFlow is built in layers — each independently useful:

| Layer | Status | What It Does |
|-------|:------:|-------------|
| **Foundation** | ✅ Done | Units, materials, geometry engine |
| **L0: Core Calculations** | 🔨 Building | Manning's, SCS hydrology, culverts, pond routing |
| **L1: Solver Wrappers** | 📋 Planned | Clean APIs over EPANET, SWMM, MODFLOW |
| **L2: Workflows** | 📋 Planned | Chain models: rain → drainage → river |
| **L3: AI & Optimization** | 📋 Planned | Parameter sweeps, calibration, LLM-ready schemas |
| **L4: Reporting** | 📋 Planned | One-script PDF/HTML engineering reports |

See [ROADMAP.md](ROADMAP.md) for the full plan.

## Requirements

- Python 3.11+
- NumPy, SciPy (the only dependencies for core calculations)

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/your-username/hydroflow.git
cd hydroflow
uv sync --all-extras

# Run tests, linting, type checking
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/hydroflow/
```

## License

MIT
