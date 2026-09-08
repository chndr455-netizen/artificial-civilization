# Artificial Civilization: World Engine (v0.1)

A procedural, text-based simulation engine modeling interacting natural systems on a 10 × 10 spatial grid.

Developed according to the **World Engine Technical Project Blueprint (Version 0.1 → 1.0)**.

---

## What is World Engine v0.1?

World Engine v0.1 creates a foundational, deterministic natural environment with four interacting physical systems:
1. **Weather System**: Atmospheric seasonal cycles, daily weather fronts, temperature lapse rates with elevation, and orographic rainfall.
2. **Water / Hydrology System**: Canopy interception, soil infiltration capacity, surface runoff, and evapotranspiration.
3. **Soil System**: Runoff-driven topsoil erosion, organic matter decomposition, and soil depth evolution.
4. **Vegetation System**: Logistic biomass growth governed by temperature, moisture, fertility, and canopy carrying capacity; drought and frost stress.

No AI agents, no economy, and no graphics are needed yet. The goal of v0.1 is to establish a **truthful causal world state**.

```text
Forest ↓
→ Canopy & Root Infiltration ↓
→ Surface Runoff ↑
→ Topsoil Erosion ↑
→ Soil Depth & Fertility ↓
→ Vegetation Growth ↓
```

---

## Running Locally on Your Linux Laptop

### Prerequisites
- Python 3.8+ (standard library only; **no external pip packages required**!)
- Linux terminal (Ubuntu, Debian, Fedora, Arch, etc.)

### Quick Start

1. Open your terminal and navigate to the project folder:
   ```bash
   cd artificial_civilization
   ```

2. Run the interactive World Engine CLI:
   ```bash
   python3 main.py
   ```

3. Run the automated unit tests:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```

4. Run the Deforestation Experiment (Section 20 of Blueprint):
   ```bash
   python3 -m experiments.deforestation
   ```

---

## Interactive CLI Commands

Inside `python3 main.py`:

- `tick [N]`: Advance simulation clock by `N` days (e.g., `tick 10` or `tick 365`).
- `inspect <x> <y>`: Inspect all physical parameters of a geographical cell (e.g., `inspect 5 5`).
- `map [layer]`: Render a 10x10 ASCII map of the world.
  - Available layers: `vegetation`, `moisture`, `erosion`, `elevation`, `fertility`
- `cut <x> <y> [cover]`: Trigger a human intervention (clear forest at cell `x, y` to `0.15`).
- `status`: Show current world day and global average metrics.
- `experiment`: Run the two-world Deforestation Causality Experiment (World A Control vs. World B Intervention).
- `help`: Display help menu.
- `quit`: Exit simulation.

---

## Project Structure

```text
artificial_civilization/
├── main.py                  # Interactive CLI entrypoint
├── README.md                # Project documentation & Linux setup guide
├── world/
│   ├── __init__.py
│   ├── cell.py              # Canonical Cell dataclass & physical bounds
│   └── world.py             # World state, 10x10 spatial grid, tick loop
├── systems/
│   ├── __init__.py
│   ├── weather.py           # Temperature & rainfall dynamics
│   ├── water.py             # Hydrology, infiltration, runoff, evapotranspiration
│   ├── soil.py              # Erosion & fertility dynamics
│   └── vegetation.py        # Biomass growth & environmental stress
├── experiments/
│   ├── __init__.py
│   └── deforestation.py     # Experiment 1: Dual-world comparative test
└── tests/
    ├── __init__.py
    └── test_world.py        # Verification of invariants, determinism, & causality
```
