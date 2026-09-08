# World Engine v0.2: Spatial Water Foundation

This release upgrades the Python World Engine from independent-cell runoff to a small spatial landscape model.

## Implemented

- Four-way (north, east, south, west) neighbor lookup.
- Terrain slope calculated from the elevation difference between neighboring cells and the configured cell size.
- Local rainfall, soil infiltration, evaporation, and surface-water storage measured in millimetres.
- Deterministic, two-phase downhill routing: every cell calculates an outflow from the same daily snapshot, then all transfers are applied together.
- Watershed outlets on world edges and a conservation diagnostic that records rainfall input, evapotranspiration, exported water, stored water, and numerical residual.
- Flow accumulation state used to identify visual river channels.
- Erosion that responds to terrain slope and routed flow rather than absolute elevation.

## Deliberately not included yet

- Dynamic terrain carving, sediment deposition, lakes, groundwater, or calibrated real-world hydrology.
- The TypeScript interface from the original archive. It remains a separate prototype because it has an independent simulation implementation. Do not compare its numerical output with this Python engine until both use one shared world state.

## Verification

Run the suite from this directory:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

The tests cover reproducibility, bounds, deforestation causality, neighbor-derived slope, downhill water transfer, and water-balance conservation.
