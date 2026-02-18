Here are the specific additions and refinements for your `ROADMAP.md` to cover those four critical milestones (A-D).

I have designed these to fit into your existing "Phase" structure, while expanding the scope to make `HydroFlow` a globally capable, enterprise-ready solution.

### 1. Update to Phase 1.1: The "Universal" Materials Engine (Milestone A)

*Replace the existing `hydroflow.materials` entry in the **Phase 1: Foundation** table with this expanded definition. This addresses the "Project vs. Company" overrides and "International Standards" requirement.*

| Module | Description | Priority |
| --- | --- | --- |
| `hydroflow.standards` | **Global Standards Governance.** Manage jurisdiction-specific defaults. `hf.set_standard("US_EPA")`, `hf.set_standard("DIN_1988")` (Germany), `hf.set_standard("JIS")` (Japan). Sets default fluid properties, safety factors, and material lookups automatically. | P0 |
| `hydroflow.materials` | **Intelligent Material Database.** <br>

<br>1. **Multi-Source:** Includes values from Chow, HEC-22, DVGW, ISO. <br>

<br>2. **Context-Aware:** `roughness("concrete", condition="old_sewer")` vs `roughness("concrete", condition="new_smooth")`. <br>

<br>3. **Hierarchical Config:** Resolves values in order: *Project Config (runtime)* → *Firm Config (json)* → *Regional Standard* → *Library Default*. | P0 |

### 2. Update to Phase 4: Professional Reporting (Milestone C)

*Add these specific bullets to the **Phase 4: Reporting** deliverables. This ensures the output is "billable" and legally usable.*

**Enhanced Reporting Deliverables:**

* [ ] **Firm Branding Engine:** Configuration to inject Company Logo, Disclaimer, and Professional Seal/Stamp placeholders automatically into every PDF.
* [ ] **Audit Trail:** Reports include a "Run Metadata" footer (HydroFlow version, Timestamp, User, Input File Hash) for legal traceability.
* [ ] **Jurisdiction Toggle:** Report templates auto-switch terminology based on settings (e.g., "Catch Basin" vs. "Gully", "Detention" vs. "Attenuation").

### 3. New Phase: Phase 6 — The "Real World" Integrations (Milestone B & D)

*I recommend adding a completely new Phase 6. This is where the tool connects to CAD and GIS, making it indispensable.*

## Phase 6: Integrations — CAD, GIS & BIM (Milestone B & D)

**Goal:** Break the silo. Engineers work in maps (GIS) and drawings (CAD). HydroFlow must read their geometry and write back their results.

### Layer 5: Interoperability

| Module | Description |
| --- | --- |
| `hydroflow.gis` | **Bi-directional GIS.** <br>

<br>• Read: Shapefiles/GeoJSON → `WaterNetwork` / `Watershed` objects. <br>

<br>• Write: Model results → Styled GeoJSON (e.g., pipes color-coded by velocity) for instant QGIS visualization. |
| `hydroflow.cad` | **The "Drafting" Bridge.** <br>

<br>• **DXF Parsing:** Extract pipe network geometry directly from raw CAD lines on specific layers (`"STORM_PIPES"`). <br>

<br>• **LandXML:** Import/Export surfaces and pipe networks using the civil engineering industry standard format (Civil 3D / 12d / Microstation compatible). |
| `hydroflow.bim` | **IFC Hooks (Stretch).** Basic export of pipes/manholes to IFC format for Revit/BIM coordination. |

### Phase 6 Deliverables

* [ ] **QGIS Plugin (Official):** A GUI panel in QGIS to run HydroFlow models directly on map layers.
* [ ] **DXF → Model Converter:** "Select CAD file, select layer names, get a runnable model."
* [ ] **Civil 3D Workflow:** LandXML support to round-trip data with Autodesk Civil 3D.

---

### 4. Updates to "Cross-Cutting Principles"

*Add this section to explain the "Project Overrides" logic you requested.*

### Configuration Hierarchy (The "Override" Law)

To support both rigid corporate standards and messy renovation projects, all physical constants are resolved using this "Waterfall" priority:

1. **Explicit Runtime Override:** `Pipe(..., roughness=0.015)` — User manually typed a value. (Highest Priority)
2. **Project Config:** `hf.load_project_config("project_settings.toml")` — Specific to this job (e.g., "This site uses 50-year-old brick sewers").
3. **Firm Config:** `~/.hydroflow/firm_config.toml` — "At Acme Corp, we always use n=0.013 for concrete."
4. **Regional Standard:** `hf.set_standard("EU")` — Loads defaults from EN/ISO norms.
5. **Library Default:** The safe fallback (usually Chow/EPA values).

## Excel Importer

Discussion Point: Excel Importer for company measured coefficients / values for concrete flumes, weirs etc for custom json files