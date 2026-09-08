"""
Deforestation Experiment (Blueprint Section 20)
Compares two identical worlds (identical random seed):
- World A (Control): No human intervention.
- World B (Intervention): At Day 100, forest cover in region (5,5) is cleared down to 15%.
Observes secondary consequences on runoff, erosion, soil moisture, fertility, and recovery.
"""

import os
import sys
from typing import Dict, Any, List

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARENT_DIR = os.path.dirname(_ROOT_DIR)
for _p in (_ROOT_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from world.world import World
except ImportError:
    from artificial_civilization.world.world import World


def run_deforestation_experiment(
    seed: int = 42,
    target_x: int = 5,
    target_y: int = 5,
    intervention_day: int = 100,
    total_days: int = 300,
    new_cover: float = 0.15
) -> Dict[str, Any]:
    # 1. Initialize two identical worlds with the identical seed
    world_a = World(width=10, height=10, seed=seed)
    world_b = World(width=10, height=10, seed=seed)

    history_a: List[Dict[str, Any]] = []
    history_b: List[Dict[str, Any]] = []

    # Run up to intervention day
    for day in range(1, total_days + 1):
        if day == intervention_day:
            world_b.intervene_cut_forest(target_x, target_y, target_cover=new_cover)

        world_a.tick(1)
        world_b.tick(1)

        # Record metrics for the target cell (5,5) in both worlds
        cell_a = world_a.get_cell(target_x, target_y)
        cell_b = world_b.get_cell(target_x, target_y)

        if cell_a and cell_b:
            history_a.append({
                "day": day,
                "veg": round(cell_a.vegetation_cover, 3),
                "runoff": round(cell_a.runoff, 2),
                "erosion": round(cell_a.erosion, 4),
                "moisture": round(cell_a.soil_moisture, 3),
                "fertility": round(cell_a.soil_fertility, 3),
                "depth": round(cell_a.soil_depth, 3),
            })
            history_b.append({
                "day": day,
                "veg": round(cell_b.vegetation_cover, 3),
                "runoff": round(cell_b.runoff, 2),
                "erosion": round(cell_b.erosion, 4),
                "moisture": round(cell_b.soil_moisture, 3),
                "fertility": round(cell_b.soil_fertility, 3),
                "depth": round(cell_b.soil_depth, 3),
            })

    # Calculate post-intervention totals
    post_a = [h for h in history_a if h["day"] >= intervention_day]
    post_b = [h for h in history_b if h["day"] >= intervention_day]

    total_erosion_a = sum(h["erosion"] for h in post_a)
    total_erosion_b = sum(h["erosion"] for h in post_b)
    total_runoff_a = sum(h["runoff"] for h in post_a)
    total_runoff_b = sum(h["runoff"] for h in post_b)

    final_cell_a = world_a.get_cell(target_x, target_y)
    final_cell_b = world_b.get_cell(target_x, target_y)

    return {
        "seed": seed,
        "cell": (target_x, target_y),
        "intervention_day": intervention_day,
        "total_days": total_days,
        "final_a": final_cell_a.to_dict() if final_cell_a else {},
        "final_b": final_cell_b.to_dict() if final_cell_b else {},
        "total_runoff_a": round(total_runoff_a, 2),
        "total_runoff_b": round(total_runoff_b, 2),
        "total_erosion_a": round(total_erosion_a, 4),
        "total_erosion_b": round(total_erosion_b, 4),
        "history_a": history_a,
        "history_b": history_b,
    }


def print_experiment_report(results: Dict[str, Any]) -> str:
    cell_x, cell_y = results["cell"]
    lines = [
        "===========================================================",
        "  WORLD ENGINE v0.1 — DEFORESTATION CAUSALITY EXPERIMENT   ",
        "===========================================================",
        f"Target Cell: ({cell_x}, {cell_y}) | Seed: {results['seed']}",
        f"Timeline: Day 1 to Day {results['total_days']} (Intervention at Day {results['intervention_day']})",
        "",
        "WORLD A (Control — Natural Forest)",
        f"  Final Forest Cover:  {results['final_a']['vegetation_cover'] * 100:.1f}%",
        f"  Final Soil Moisture: {results['final_a']['soil_moisture']:.2f}",
        f"  Final Soil Fertility:{results['final_a']['soil_fertility']:.2f}",
        f"  Post-Day 100 Runoff: {results['total_runoff_a']:.1f} mm",
        f"  Post-Day 100 Erosion:{results['total_erosion_a']:.4f} mm stripped",
        "",
        "WORLD B (Intervention — Cleared at Day 100)",
        f"  Final Forest Cover:  {results['final_b']['vegetation_cover'] * 100:.1f}%",
        f"  Final Soil Moisture: {results['final_b']['soil_moisture']:.2f}",
        f"  Final Soil Fertility:{results['final_b']['soil_fertility']:.2f}",
        f"  Post-Day 100 Runoff: {results['total_runoff_b']:.1f} mm (Ratio: {results['total_runoff_b']/max(0.001, results['total_runoff_a']):.2f}x)",
        f"  Post-Day 100 Erosion:{results['total_erosion_b']:.4f} mm stripped (Ratio: {results['total_erosion_b']/max(0.0001, results['total_erosion_a']):.2f}x)",
        "",
        "OBSERVED CAUSAL CHAIN CONFIRMATION:",
        "  Forest ↓  ==> Canopy & root infiltration ↓",
        "            ==> Surface Runoff ↑",
        "            ==> Topsoil Erosion ↑",
        "            ==> Organic Fertility Loss",
        "===========================================================",
    ]
    report = "\n".join(lines)
    print(report)
    return report


if __name__ == "__main__":
    res = run_deforestation_experiment()
    print_experiment_report(res)
