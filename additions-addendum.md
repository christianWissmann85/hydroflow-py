
 ▐▛███▜▌   Claude Code v2.1.44
▝▜█████▛▘  Opus 4.6 · Claude Max
  ▘▘ ▝▝    ~/hydroflow

✻ Conversation compacted (ctrl+o for history)


❯ /compact
  ⎿  Compacted (ctrl+o to see full summary)
  ⎿  Read pyproject.toml (103 lines)
  ⎿  Read .github/workflows/ci.yml (39 lines)
  ⎿  Read .github/workflows/publish.yml (47 lines)
  ⎿  Referenced file dist/hydroflow-0.1.0-py3-none-any.whl
  ⎿  Read LICENSE (22 lines)

❯ Alright, let us now please discuss the proposed @roadmap-additions.md that Gemini did suggest we should look into. It sounds like all are great and make a lot of sense!
  Lets please think about this, and deploy task agents for web search exploration and local codebase exploration.
  ⎿  Read roadmap-additions.md (74 lines)

● Great idea, Chris! 🧠 Let me re-read the roadmap additions and then deploy agents to research both the landscape and our codebase in parallel.

● Read 1 file (ctrl+o to expand)

● Now let me also check the existing roadmap and codebase, then deploy research agents in parallel.

● 2 agents launched (ctrl+o to expand)
   ├─ Task (Research international hydraulic standards)
   │  ⎿  Running in the background (shift+↑ to manage)
   └─ Explore (Explore codebase for roadmap planning)
      ⎿  Running in the background (shift+↑ to manage)

● Searched for 1 pattern, read 1 file (ctrl+o to expand)

● Good, I've got the full ROADMAP.md and the roadmap-additions.md. Both research agents are working in the background — let me wait for their findings before we discuss. ⏳

● Task Output af30ac4
  ⎿  Task is still running…

● Task Output a241657
  ⎿  Read output (ctrl+o to expand)

● The codebase exploration agent is done. The web research agent is still running — let me check on it.

● Task Output af30ac4
  ⎿  Read output (ctrl+o to expand)

● Both agents are done! Let me get their final summary reports.

● Searched for 3 patterns, read 2 files (ctrl+o to expand)

● Let me extract the final response text from both agents.

● Bash(python3 -c "
      import json…)
  ⎿  Now I have gathered comprehensive information across all four research areas. Let me compile the structured report.

     ---
     … +45 lines (ctrl+o to expand)

● Bash(python3 -c "
      import json…)
  ⎿  Perfect! I now have all the information I need. Let me compile the comprehensive architectural overview:

     ---
     … +45 lines (ctrl+o to expand)

● Excellent! Both agents delivered rich findings. Let me get the remaining sections of the web research.

● Bash(python3 -c "
      import json…)
  ⎿  Now I have gathered comprehensive information across all four research areas. Let me compile the structured report.

     ---
     … +69 lines (ctrl+o to expand)

● Bash(python3 -c "
      import json…)
  ⎿  ## 3. GIS / CAD Python Libraries

     ### 3.1 GIS Stack (Shapefiles / GeoJSON)
     … +61 lines (ctrl+o to expand)

● Now I have a complete picture. Let me synthesize all the research into a structured discussion for you, Chris! 🧠

  ---
  Roadmap Additions Analysis

  Here's my take on each of Gemini's four proposals, informed by the codebase exploration and web research:

  ---
  1. Universal Materials Engine (hydroflow.standards + enhanced hydroflow.materials) — Milestone A

  Verdict: Strongly agree, but with a phased approach 🟢

  What we have today:
  - materials.py has a flat MANNING_ROUGHNESS dict with ~30 materials (Chow + HEC-22 sources)
  - pressure.py has HAZEN_WILLIAMS_C and MINOR_LOSS_K dicts (also hardcoded)
  - No config files, no hierarchy, no condition-awareness

  What the research found:
  - Roughness data is freely available from published sources (EPA, HEC-22, Engineering Toolbox) — we're safe to compile comprehensive tables
  - No existing Python library does multi-standard profiles — fluids has material data but no regional switching. This is a genuine differentiator.
  - The roughness values carry ±30-50% uncertainty and change dramatically with pipe age/condition — context-awareness is genuinely valuable (not just over-engineering)
  - EU/German (DIN, DVGW) and Japanese (JWWA, JIS) standard documents are proprietary, but the actual roughness coefficient values are published in textbooks and public references

  My recommendation — Phase it:

  Step: 1a
  What: Expand materials database: add Hazen-Williams C, Darcy epsilon, condition modifiers (new/old/corroded). Move from hardcoded dicts → embedded TOML/JSON data files.
  Priority: P0 (Phase 1.1)
  ────────────────────────────────────────
  Step: 1b
  What: Add roughness("concrete", condition="old_sewer") context-aware lookups
  Priority: P0 (Phase 1.1)
  ────────────────────────────────────────
  Step: 1c
  What: Configuration hierarchy: Runtime → Project TOML → Firm TOML → Library Default. Use stdlib tomllib (Python 3.11+), no heavy deps like Dynaconf needed.
  Priority: P1 (Phase 2)
  ────────────────────────────────────────
  Step: 1d
  What: hf.set_standard("US_EPA") / hf.set_standard("DIN") regional profiles
  Priority: P2 (Phase 2-3)

  Key principle: Keep zero external deps for Layer 0. Python 3.11+ has tomllib built-in — we don't need Dynaconf or OmegaConf. Simple cascading dict merges will do.

  ---
  2. Professional Reporting (Enhanced Phase 4/5) — Milestone C

  Verdict: Great ideas, but these belong later 🟡

  What the research found:
  - WeasyPrint + Jinja2 is the recommended stack: HTML/CSS templates rendered to PDF, supports logos, headers/footers, audit metadata
  - fpdf2 is simpler for basic reports, ReportLab for pixel-precise layout
  - The firm branding, audit trail, and jurisdiction toggle ideas are all technically feasible

  My take:
  The Firm Branding Engine, Audit Trail, and Jurisdiction Toggle are all excellent enterprise-readiness features, but they're squarely Phase 5 work. Right now we should:

  1. Not overthink Phase 5 yet — we haven't even started Phase 2 (EPANET wrapper)
  2. Note them in the ROADMAP as Phase 5 enhancements
  3. The Jurisdiction Toggle ("Catch Basin" vs "Gully") is a natural extension of the Standards system from Milestone A — it can share the same TOML profiles

  ---
  3. Real-World Integrations (Phase 6: CAD, GIS, BIM) — Milestone B & D

  Verdict: Valuable but ambitious. Dependency-heavy, should be strictly optional extras. 🟡

  What the research found:

  ┌─────────────┬─────────────────────────────────┬──────────────────────────┬──────────────────────────────────────┐
  │    Area     │              Stack              │         Maturity         │          Dependency Weight           │
  ├─────────────┼─────────────────────────────────┼──────────────────────────┼──────────────────────────────────────┤
  │ GIS         │ GeoPandas + Pyogrio + Shapely 2 │ Mature, production-ready │ Heavy (GDAL, etc.)                   │
  ├─────────────┼─────────────────────────────────┼──────────────────────────┼──────────────────────────────────────┤
  │ DXF/CAD     │ ezdxf v1.4                      │ Mature, MIT licensed     │ Light (pure Python + optional C ext) │
  ├─────────────┼─────────────────────────────────┼──────────────────────────┼──────────────────────────────────────┤
  │ LandXML     │ lxml + custom parser            │ No mature library exists │ Medium                               │
  ├─────────────┼─────────────────────────────────┼──────────────────────────┼──────────────────────────────────────┤
  │ BIM/IFC     │ IfcOpenShell v0.8               │ Mature                   │ Heavy (C++ bindings)                 │
  ├─────────────┼─────────────────────────────────┼──────────────────────────┼──────────────────────────────────────┤
  │ QGIS Plugin │ Processing Plugin pattern       │ Well-documented          │ Separate package                     │
  └─────────────┴─────────────────────────────────┴──────────────────────────┴──────────────────────────────────────┘

  My recommendation:
  - ezdxf (DXF parsing) is the lowest-hanging fruit — it's lightweight and MIT. A hydroflow.cad module could be a realistic Phase 3-4 addition.
  - GIS integration is valuable but brings GDAL dependency hell. Must be a strict optional extra: pip install hydroflow-py[gis]
  - LandXML is the weak spot — we'd need to write our own parser on top of lxml. Worth doing eventually but not a priority.
  - BIM/IFC is a stretch goal. IfcOpenShell's MEP/piping support is promising.
  - QGIS Plugin should be a separate repo (hydroflow-qgis) to avoid coupling.

  I'd suggest this isn't a separate "Phase 6" — instead, weave integration modules into existing phases as optional extras.

  ---
  4. Configuration Hierarchy ("Override Law") — Cross-cutting

  Verdict: Exactly right, and beautifully simple 🟢

  The 5-level waterfall makes perfect engineering sense:
  1. Explicit Runtime Override → Pipe(..., roughness=0.015)
  2. Project Config → hf.load_project_config("project.toml")
  3. Firm Config → ~/.hydroflow/firm_config.toml
  4. Regional Standard → hf.set_standard("EU")
  5. Library Default → Chow/EPA values

  This aligns perfectly with how our codebase already works:
  - Level 1 already works (you can pass roughness=0.015 to any channel/culvert)
  - Level 5 already works (MANNING_ROUGHNESS dict is the library default)
  - Levels 2-4 are the new work, and can be implemented incrementally with tomllib

  ---
  Summary: What Should We Add to the ROADMAP?

  ┌───────────────────────────────────────┬──────────────────────┬───────────────────────┬──────────┐
  │               Proposal                │       Include?       │        Where?         │ Priority │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ Context-aware materials + expanded DB │ Yes                  │ Phase 1.1 (next up!)  │ P0       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ Config hierarchy (TOML cascade)       │ Yes                  │ Phase 2               │ P1       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ Standards profiles (US/EU/JP)         │ Yes                  │ Phase 2-3             │ P2       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ Professional reporting enhancements   │ Yes                  │ Phase 5 (existing)    │ P3       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ GIS integration                       │ Yes (optional extra) │ Woven into Phases 3-5 │ P2       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ DXF/CAD integration                   │ Yes (optional extra) │ Phase 3-4             │ P2       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ LandXML parser                        │ Maybe                │ Phase 4-5             │ P3       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ BIM/IFC integration                   │ Stretch              │ Phase 5+              │ P4       │
  ├───────────────────────────────────────┼──────────────────────┼───────────────────────┼──────────┤
  │ QGIS Plugin                           │ Yes (separate repo)  │ Phase 5               │ P3       │
  └───────────────────────────────────────┴──────────────────────┴───────────────────────┴──────────┘

  What do you think, Chris? Want me to draft the actual ROADMAP.md updates incorporating these decisions? 🚀

✻ Cogitated for 6m 5s

● Agent "Explore codebase for roadmap planning" completed

● Thanks, that notification just confirms what we already reviewed. The full analysis is in my summary above!

  So Chris — what are your thoughts on the prioritization? The big questions are:

  1. Phase 1.1 — Context-aware materials as the immediate next step?
  2. Config hierarchy — stdlib tomllib vs. a heavier lib like Dynaconf?
  3. Phase 6 as separate phase vs. woven into existing phases as optional extras?

  Ready to draft the ROADMAP.md updates whenever you give the green light! 🚀

● Agent "Research international hydraulic standards" completed

● Yep, that's the web research agent confirming what's already in the analysis above. All the findings are incorporated into the summary!

  So — ball's in your court, Chris! What's your take on the priorities? 😊

❯ Excellent! I would say we first discuss the Materials feature in more detail. I want to move from the current hardcoded approach to a pure data driven approach (e.g. jsons
  or tomls) which can be version controlled, and easily integrated and updated. What do you think?

● Love this direction, Chris! 🎯 Moving to data-driven is exactly the right call — it sets the foundation for everything else (standards profiles, user overrides,
  context-awareness). Let me look at what we're working with today.

● Read 2 files (ctrl+o to expand)

● 100% agree, Chris. Here's what I see — three separate hardcoded dicts spread across two files:

  ┌───────────────────┬──────────────┬──────────────┐
  │       Data        │   Location   │   Entries    │
  ├───────────────────┼──────────────┼──────────────┤
  │ MANNING_ROUGHNESS │ materials.py │ 30 materials │
  ├───────────────────┼──────────────┼──────────────┤
  │ HAZEN_WILLIAMS_C  │ pressure.py  │ 12 materials │
  ├───────────────────┼──────────────┼──────────────┤
  │ MINOR_LOSS_K      │ pressure.py  │ 15 fittings  │
  └───────────────────┴──────────────┴──────────────┘

  The problem is obvious — "concrete" appears in both Manning's and Hazen-Williams with no link between them. An engineer working with concrete pipe needs n, C, and epsilon. These
   should live together.

  Here's my thinking on the data-driven architecture:

  ---
  JSON vs TOML for the data files?

  ┌──────────────────────────────────┬──────────────────────────┬───────────────────────────────┐
  │                                  │           JSON           │             TOML              │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ Nested data (ranges, conditions) │ Natural                  │ Verbose                       │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ Comments for sources             │ No (use metadata fields) │ Yes                           │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ Tooling / ecosystem              │ Universal                │ Narrower                      │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ Schema validation                │ JSON Schema (mature)     │ No standard                   │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ Generated by external tools      │ Easy                     │ Less common                   │
  ├──────────────────────────────────┼──────────────────────────┼───────────────────────────────┤
  │ importlib.resources loading      │ json.load() (stdlib)     │ tomllib.load() (stdlib 3.11+) │
  └──────────────────────────────────┴──────────────────────────┴───────────────────────────────┘

  My recommendation: JSON for data, TOML for config later. Material property tables are data — structured records with nested fields, ranges, and metadata. JSON handles this
  naturally. When we add user/firm/project config (Phase 2), that's where TOML shines (human-editable, supports comments for engineering decisions).

  ---
  Proposed data structure

  A unified materials.json where each material carries all its properties:

  {
    "_meta": {
      "version": "1.0.0",
      "sources": {
        "chow_1959": "Chow, V.T. (1959). Open-Channel Hydraulics, Table 5-6",
        "hec22_2009": "FHWA HEC-22 (2009), Table 3-1",
        "brater_king_1976": "Brater & King (1976). Handbook of Hydraulics"
      }
    },
    "materials": {
      "concrete": {
        "category": "closed_conduit",
        "manning_n": {
          "default": 0.013,
          "range": [0.011, 0.017],
          "source": "chow_1959"
        },
        "hazen_williams_c": {
          "default": 130,
          "range": [100, 140],
          "source": "brater_king_1976"
        },
        "darcy_epsilon_mm": {
          "default": 0.3,
          "range": [0.3, 3.0],
          "source": "brater_king_1976"
        },
        "conditions": {
          "new_smooth": {"manning_n": 0.012, "hazen_williams_c": 140},
          "old_rough": {"manning_n": 0.016, "hazen_williams_c": 100}
        }
      }
    }
  }

  And a separate fittings.json for minor loss K values:

  {
    "_meta": {
      "version": "1.0.0",
      "sources": {
        "crane_tp410": "Crane Co. (2013). TP-410, Flow of Fluids"
      }
    },
    "fittings": {
      "90_elbow": {
        "K": 0.9,
        "K_long_radius": 0.6,
        "source": "crane_tp410"
      }
    }
  }

  File layout

  src/hydroflow/
  ├── data/
  │   ├── materials.json      # All material properties (unified)
  │   ├── fittings.json       # Minor loss K values
  │   └── __init__.py         # empty (makes it a package for importlib.resources)
  ├── materials.py            # Loading logic + resolve functions (no hardcoded data)
  └── ...

  Key design decisions

  1. Loading: importlib.resources to load bundled JSON — works in wheels, editable installs, everywhere
  2. Caching: Load once on first access, cache at module level (lazy)
  3. Backwards-compatible API: resolve_roughness("concrete") keeps working identically
  4. Extensibility: Users can later load custom JSON files to extend/override (the config hierarchy from Milestone D)
  5. Zero new deps: json and importlib.resources are both stdlib

  What this unlocks immediately

  - resolve_roughness("concrete", condition="old_rough") — context-aware lookups
  - resolve_hazen_williams("pvc") — unified material module instead of scattered dicts
  - Range data exposed: engineers can see n ranges for uncertainty analysis
  - Source traceability: every value traceable to a published reference

  ---
  What do you think about this structure? The big question is whether you like:
  1. Unified materials.json (one file, all properties per material) vs split files (one per coefficient type)
  2. JSON for data + TOML for config later
  3. The conditions approach for context-awareness

✻ Cogitated for 1m 14s

❯ Excellent clean design! I love the json for data approach, good call, with toml for configs.

  What do you think would be the approach regarding your question about conditions and unified vs split jsons?

● Great question — let me lay out my reasoning on both.

  Unified vs Split: I'd go unified

  The material is the entity, not the coefficient. When an engineer says "I'm using concrete pipe," they don't think in terms of three separate lookup tables. They think:

  "Concrete pipe — what are its properties?"

  A unified materials.json reflects that mental model:

  Looking up "concrete"
  ├── Manning's n:       0.013
  ├── Hazen-Williams C:  130
  ├── Darcy epsilon:     0.3 mm
  └── all from one place, one source of truth

  Split files create drift risk. If you add a new material, you'd need to update 3 files and keep them in sync. With a unified file, it's one edit, one entry, one review.

  For materials that only have some properties (e.g., floodplain_grass has Manning's n but no Hazen-Williams C — it's not a pipe), we simply omit those fields. The schema makes
  them optional.

  Fittings stay separate though — they're not materials, they're geometric configurations (elbows, valves, entrances). Different entity, different file.

  Conditions: Material-level partial overrides

  I considered two approaches:

  Option A — Conditions per property:
  "manning_n": {
    "default": 0.013,
    "conditions": {"new_smooth": 0.012, "old_rough": 0.016}
  },
  "hazen_williams_c": {
    "default": 130,
    "conditions": {"new": 140, "old": 100}
  }

  Option B — Conditions per material (partial overrides):
  "manning_n": {"default": 0.013, "range": [0.011, 0.017]},
  "hazen_williams_c": {"default": 130, "range": [100, 140]},
  "darcy_epsilon_mm": {"default": 0.3, "range": [0.3, 3.0]},
  "conditions": {
    "new_smooth": {"manning_n": 0.012, "hazen_williams_c": 140},
    "old_rough":  {"manning_n": 0.016, "hazen_williams_c": 100, "darcy_epsilon_mm": 1.5}
  }

  I'd go with Option B. Here's why:

  When an engineer says "this is old rough concrete", they want all properties to shift coherently — rougher n, lower C, higher epsilon. You don't want them reasoning about
  conditions per-property independently.

  The key insight: conditions are partial overrides that merge with defaults. If old_rough only specifies manning_n and hazen_williams_c, the darcy_epsilon_mm falls through to the
   material's default. This is exactly the same "waterfall" principle as the config hierarchy we discussed earlier:

  condition override → material default → (later: firm config → standard → library)

  What the API would look like

  # Backwards compatible — works exactly like today
  resolve_roughness("concrete")                        # → 0.013

  # Context-aware — new capability
  resolve_roughness("concrete", condition="old_rough")  # → 0.016

  # Full material lookup — new unified access
  mat = get_material("concrete")
  mat.manning_n          # → 0.013
  mat.hazen_williams_c   # → 130
  mat.darcy_epsilon_mm   # → 0.3

  mat = get_material("concrete", condition="old_rough")
  mat.manning_n          # → 0.016  (overridden)
  mat.hazen_williams_c   # → 100    (overridden)
  mat.darcy_epsilon_mm   # → 1.5    (overridden)

  # Range data for uncertainty analysis
  mat = get_material("pvc")
  mat.manning_n_range    # → (0.008, 0.011)

  So the final structure for materials.json:

  {
    "_meta": {
      "version": "1.0.0",
      "description": "HydroFlow material properties database",
      "sources": {
        "chow_1959": "Chow, V.T. (1959). Open-Channel Hydraulics, Table 5-6",
        "hec22_2009": "FHWA HEC-22 (2009), Table 3-1",
        "brater_king_1976": "Brater & King (1976). Handbook of Hydraulics"
      }
    },
    "materials": {
      "concrete": {
        "category": "closed_conduit",
        "description": "Standard concrete pipe",
        "manning_n": {"default": 0.013, "range": [0.011, 0.017], "source": "chow_1959"},
        "hazen_williams_c": {"default": 130, "range": [100, 140], "source": "brater_king_1976"},
        "darcy_epsilon_mm": {"default": 0.3, "range": [0.3, 3.0], "source": "brater_king_1976"},
        "conditions": {
          "new_smooth": {"manning_n": 0.012, "hazen_williams_c": 140, "darcy_epsilon_mm": 0.3},
          "old_rough": {"manning_n": 0.016, "hazen_williams_c": 100, "darcy_epsilon_mm": 1.5}
        }
      },
      "floodplain_grass": {
        "category": "open_channel_unlined",
        "description": "Grass-covered floodplain",
        "manning_n": {"default": 0.035, "range": [0.025, 0.050], "source": "chow_1959"}
      }
    }
  }

  Notice how floodplain_grass simply has no hazen_williams_c or darcy_epsilon_mm — it's an open channel, not a pipe. Clean and natural.

  Want me to start planning the implementation? 🚀

✻ Cooked for 58s

❯ Wow, what an elegant data designt! Yes, let's plan the implementation please 😊! It should include how we actually get the data, and how can use task agents to add entries
  to our tobe created json database. It might get huge 😅

● Entered plan mode
  Claude is now exploring and designing an implementation approach.

● Let me explore the codebase to nail down the implementation details.

● 2 agents launched (ctrl+o to expand)
   ├─ Explore (Explore materials usage patterns)
   │  ⎿  Running in the background (shift+↑ to manage)
   └─ Task (Research material data sources)
      ⎿  Running in the background (shift+↑ to manage)

● Good, both agents are running — one exploring the codebase patterns, the other compiling material data from engineering references. Let me wait for them to finish before
  designing the plan.

● Task Output a31d6df
  ⎿  Read output (ctrl+o to expand)

● Task Output a93583c
  ⎿  Read output (ctrl+o to expand)

● Let me get the final findings from both agents.

● Bash(python3 -c "
      import json…)
  ⎿  Perfect! Now I have all the information I need. Let me compile the comprehensive report:

     ---
     … +69 lines (ctrl+o to expand)

● Bash(python3 -c "
      import json…)
  ⎿  # Comprehensive Water Engineering Roughness & Loss Coefficient Database

     Below is the compiled reference data, organized for direct JSON conversion. Sources are abbreviated and listed at the end.
     … +86 lines (ctrl+o to expand)

● Excellent data from both agents! Now I have the complete picture. Let me design the implementation plan.

● Plan(Design materials implementation plan)
  ⎿  Done (27 tool uses · 74.3k tokens · 6m 20s)
  (ctrl+o to expand)

● The Plan agent delivered a thorough design. Let me review the critical files and then write the final plan.

● Read 2 files (ctrl+o to expand)

● Good, I have the full picture. Now let me write the implementation plan.

● Updated plan
  ⎿  /plan to preview

● Plan is written! Here's the summary:

  7 steps, ~11 files — the core idea is:
  1. Create src/hydroflow/data/ with materials.json and fittings.json
  2. Add MaterialProperties / FittingProperties dataclasses to _types.py
  3. Rewrite materials.py as a JSON-backed loader with get_material(), get_fitting(), and backwards-compat resolve_roughness()
  4. Wire pressure.py to delegate lookups to the new module
  5. Update __init__.py exports (lazy-load deprecated dicts)
  6. Comprehensive tests (data integrity + API + regression)
  7. Build verification

  The alias mechanism ensures every existing key like "concrete_smooth" or "ductile_iron_new" still works by mapping to the new material + condition structure.

  For populating the JSON — we'll seed from existing hardcoded data first (exact backwards compat), then launch 3 parallel task agents to expand with the ~70 materials and ~30
  fittings from the research.

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Plan: Data-Driven Material Properties Migration

 Context

 HydroFlow's material data (roughness coefficients, Hazen-Williams C, minor loss K) is currently hardcoded in Python dicts across two files. This makes it hard to update, extend,
  or version-control independently. We're migrating to a JSON data-driven approach where all material properties live in structured JSON files that can be easily reviewed,
 extended, and eventually overridden by user/project configs.

 This is Phase 1.1 of the roadmap — the foundation for the future Standards & Config Hierarchy system.

 Files Changed

 ┌───────────────────────────────────┬───────────┬───────────────────────────────────────────────────────────────────────┐
 │               File                │  Action   │                              Description                              │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/data/__init__.py    │ CREATE    │ Empty package marker for importlib.resources                          │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/data/materials.json │ CREATE    │ Unified material database (~40+ materials, conditions, ranges)        │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/data/fittings.json  │ CREATE    │ Minor loss K fitting database (~30+ fittings)                         │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/_types.py           │ MODIFY    │ Add MaterialProperties and FittingProperties dataclasses              │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/materials.py        │ REWRITE   │ JSON loader, get_material(), get_fitting(), backwards-compat wrappers │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/pressure.py         │ MODIFY    │ Remove hardcoded dicts, delegate lookups to materials.py              │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ src/hydroflow/__init__.py         │ MODIFY    │ Add new exports, lazy-load deprecated dicts via __getattr__           │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ tests/test_data_integrity.py      │ CREATE    │ JSON schema/range/source validation                                   │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ tests/test_material_api.py        │ CREATE    │ Tests for get_material(), get_fitting(), conditions                   │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ tests/test_materials.py           │ NO CHANGE │ Must pass as-is (backwards compat)                                    │
 ├───────────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
 │ tests/test_pressure.py            │ NO CHANGE │ Must pass as-is (backwards compat)                                    │
 └───────────────────────────────────┴───────────┴───────────────────────────────────────────────────────────────────────┘

 Implementation Steps

 Step 1: Create src/hydroflow/data/ package + JSON files

 1a. Create src/hydroflow/data/__init__.py (empty).

 1b. Create src/hydroflow/data/materials.json with this structure:
 {
   "_meta": {
     "version": "1.0.0",
     "sources": { "chow_1959": "Chow, V.T. (1959)...", ... },
     "aliases": {
       "concrete_smooth": {"material": "concrete", "condition": "new_smooth"},
       "concrete_rough": {"material": "concrete", "condition": "old_rough"},
       "ductile_iron_new": {"material": "ductile_iron", "condition": "cement_lined"},
       ...
     }
   },
   "materials": {
     "concrete": {
       "category": "closed_conduit",
       "description": "Standard concrete pipe",
       "manning_n": {"default": 0.013, "range": [0.011, 0.017], "source": "chow_1959"},
       "hazen_williams_c": {"default": 130, "range": [100, 140], "source": "brater_king_1976"},
       "darcy_epsilon_mm": {"default": 0.3, "range": [0.3, 3.0], "source": "brater_king_1976"},
       "conditions": {
         "new_smooth": {"manning_n": 0.012, "hazen_williams_c": 140, "darcy_epsilon_mm": 0.3},
         "old_rough": {"manning_n": 0.016, "hazen_williams_c": 100, "darcy_epsilon_mm": 1.5}
       }
     }
   }
 }

 The aliases map enables backwards compatibility: resolve_roughness("concrete_smooth") resolves to get_material("concrete", condition="new_smooth").manning_n. This preserves
 every existing key from MANNING_ROUGHNESS, HAZEN_WILLIAMS_C, etc.

 1c. Create src/hydroflow/data/fittings.json with similar structure for minor loss K values.

 1d. Use parallel task agents to populate the full data:
 - Agent 1: Closed conduit materials (~15 materials with conditions) — data already compiled by research agent
 - Agent 2: Open channel materials (~15 materials with conditions)
 - Agent 3: Fittings (~30 fitting types)

 Each agent writes directly to the JSON file. We validate with data integrity tests afterward.

 Step 2: Add dataclasses to _types.py

 Add MaterialProperties and FittingProperties following the existing SectionProperties pattern (@dataclass(frozen=True, slots=True)):

 @dataclass(frozen=True, slots=True)
 class MaterialProperties:
     name: str
     category: str
     description: str
     manning_n: float
     manning_n_range: tuple[float, float] | None = None
     hazen_williams_c: float | None = None
     hazen_williams_c_range: tuple[float, float] | None = None
     darcy_epsilon_mm: float | None = None
     darcy_epsilon_mm_range: tuple[float, float] | None = None
     condition: str | None = None

 @dataclass(frozen=True, slots=True)
 class FittingProperties:
     name: str
     category: str
     description: str
     K: float
     K_range: tuple[float, float] | None = None
     condition: str | None = None

 Step 3: Rewrite materials.py

 Replace the hardcoded MANNING_ROUGHNESS dict with a JSON-backed module:

 Core loading (lazy, cached):
 _materials_cache: dict[str, Any] | None = None

 def _load_materials() -> dict[str, Any]:
     global _materials_cache
     if _materials_cache is None:
         ref = resources.files("hydroflow.data").joinpath("materials.json")
         _materials_cache = json.loads(ref.read_text(encoding="utf-8"))
     return _materials_cache

 New public API:
 - get_material(name, *, condition=None) -> MaterialProperties — unified lookup with condition overrides and fuzzy matching
 - get_fitting(name, *, condition=None) -> FittingProperties — same for fittings
 - list_materials() -> list[str] — list all material keys
 - list_fittings() -> list[str] — list all fitting keys

 Backwards-compatible resolve_roughness():
 Add keyword-only condition parameter (backwards-safe since all 5 existing call sites pass roughness positionally):
 def resolve_roughness(roughness: float | str, *, condition: str | None = None) -> float:

 Shared fuzzy matching:
 Extract a _fuzzy_lookup() helper (generalizes the current difflib logic) used by get_material(), get_fitting(), and resolve functions.

 Legacy dict generation:
 Computed properties that build dict[str, float] from JSON data (for MANNING_ROUGHNESS, HAZEN_WILLIAMS_C, MINOR_LOSS_K). Exposed via module __getattr__ for lazy loading.

 Step 4: Update pressure.py

 - Remove HAZEN_WILLIAMS_C and MINOR_LOSS_K hardcoded dicts
 - Import _resolve_hazen_williams() and _resolve_minor_loss() helpers from materials.py
 - Replace inline dict lookups in hazen_williams() (line 252) and minor_loss() (line 302) with calls to these helpers
 - Add __getattr__ for lazy backwards-compat access to the removed dicts

 Step 5: Update __init__.py

 - Add new imports: get_material, get_fitting, list_materials, list_fittings, MaterialProperties, FittingProperties
 - Remove direct imports of MANNING_ROUGHNESS, HAZEN_WILLIAMS_C, MINOR_LOSS_K (they trigger loading at import time)
 - Add __getattr__ to lazy-proxy the three deprecated dict names
 - Update __all__ with the new public names

 Step 6: Tests

 6a. tests/test_data_integrity.py (NEW):
 - Every material has required fields (category, manning_n)
 - range[0] <= default <= range[1] for all properties
 - Source keys reference valid entries in _meta.sources
 - Condition overrides fall within parent material's declared range
 - Aliases point to valid material + condition combinations
 - Same validation for fittings

 6b. tests/test_material_api.py (NEW):
 - get_material("concrete") returns correct defaults
 - get_material("concrete", condition="old_rough") applies overrides
 - get_material("concrete_smooth") resolves via alias
 - get_material("floodplain_grass").hazen_williams_c is None
 - Fuzzy matching suggests close matches
 - Unknown condition raises ValueError
 - get_fitting("90_elbow") returns correct K
 - list_materials() returns sorted list

 6c. Existing tests pass unchanged:
 - test_materials.py — resolve_roughness() same behavior
 - test_pressure.py — hazen_williams(C="pvc") and minor_loss(K="90_elbow") same behavior

 Step 7: Build verification

 Hatchling auto-includes non-Python files in the package tree — JSON files in src/hydroflow/data/ will be bundled. Verify by checking wheel contents after uv build.

 Task Agent Strategy for JSON Population

 The compiled data from the research agent covers ~25 closed conduits, ~12 open channels, and ~30 fittings. Implementation approach:

 1. First: Manually seed materials.json with the ~30 existing entries from hardcoded dicts (ensures exact backwards compat)
 2. Then: Launch 3 parallel task agents to expand the database:
   - Agent 1: Add remaining closed conduit materials with full conditions (using research data)
   - Agent 2: Add remaining open channel materials with conditions
   - Agent 3: Add all fittings to fittings.json
 3. Finally: Run data integrity tests to validate everything

 Verification

 # Run full test suite (existing + new)
 uv run pytest tests/ -v

 # Verify backwards compatibility specifically
 uv run pytest tests/test_materials.py tests/test_pressure.py -v

 # Verify data integrity
 uv run pytest tests/test_data_integrity.py -v

 # Lint + type check
 uv run ruff check src/ tests/
 uv run mypy src/hydroflow/

 # Build and verify JSON files are included
 uv build && python -c "import zipfile; z=zipfile.ZipFile('dist/hydroflow_py-0.1.0-py3-none-any.whl'); print([f for f in z.namelist() if 'data' in f])"
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

 Claude has written up a plan and is ready to execute. Would you like to proceed?

 ❯ 1. Yes, clear context and auto-accept edits (shift+tab)
   2. Yes, auto-accept edits
   3. Yes, manually approve edits
   4. Type here to tell Claude what to change

 ctrl-g to edit in VS Code · ~/.claude/plans/parsed-dreaming-music.md
