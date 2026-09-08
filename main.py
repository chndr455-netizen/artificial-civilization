"""
World Engine v0.2 — Main Interactive CLI
Entry point for running the simulation on a local Linux laptop.
"""

import sys
import os

# Automatically ensure current folder and parent folder are in sys.path
# so running `python3 main.py` directly from inside the folder works seamlessly
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_CURRENT_DIR)
for _p in (_CURRENT_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from world.world import World
    from experiments.deforestation import run_deforestation_experiment, print_experiment_report
except ImportError:
    from artificial_civilization.world.world import World
    from artificial_civilization.experiments.deforestation import run_deforestation_experiment, print_experiment_report


def print_banner():
    print("""
===========================================================
      ARTIFICIAL CIVILIZATION: WORLD ENGINE v0.2
  Procedural, Text-Based Natural World Simulation Engine
===========================================================
  Systems: Weather • Hydrology • Soil & Erosion • Vegetation
  Spatial Scale: 10 x 10 Cells (1 km² territory)
  Type 'help' for command list.
===========================================================
""")


def print_help():
    print("""
Available Commands:
  tick [N]                 Advance world by N days (default 1)
  inspect <x> <y>          Inspect environmental state of cell (x, y)
  map [layer]              Display 10x10 ASCII grid map
                           Layers: vegetation (default), moisture, erosion, elevation, fertility, flow, slope
  cut <x> <y> [cover]      Human intervention: cut forest at (x, y) to cover (default 0.15)
  status                   Display current world day & global average metrics
  experiment               Run Experiment 1: Deforestation comparison (World A vs B)
  help                     Show this help guide
  quit / exit              Exit simulation
""")


def run_cli():
    print_banner()
    world = World(width=10, height=10, seed=12345)
    print(f"World initialized. Simulation clock: Day {world.day}.\n")
    print(world.render_ascii_map("vegetation"))
    print("\nTip: Try typing 'tick 10' or 'inspect 5 5' or 'experiment'.\n")

    while True:
        try:
            line = input(f"[Day {world.day}] world-engine> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting World Engine. Goodbye.")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("quit", "exit", "q"):
            print("Shutting down World Engine. Goodbye.")
            break

        elif cmd == "help":
            print_help()

        elif cmd in ("tick", "step"):
            days = 1
            if args:
                try:
                    days = int(args[0])
                    if days <= 0:
                        print("Error: Days must be a positive integer.")
                        continue
                except ValueError:
                    print("Error: Invalid number of days.")
                    continue
            print(f"Advancing simulation by {days} day(s)...")
            world.tick(days)
            print(f"Current Clock: Day {world.day}")

        elif cmd == "inspect":
            if len(args) < 2:
                print("Usage: inspect <x> <y>   (e.g., inspect 5 5)")
                continue
            try:
                x, y = int(args[0]), int(args[1])
                print(world.inspect(x, y))
            except ValueError:
                print("Error: Coordinates x and y must be integers between 0 and 9.")

        elif cmd == "map":
            layer = args[0].lower() if args else "vegetation"
            valid_layers = ("vegetation", "moisture", "erosion", "elevation", "fertility", "flow", "slope")
            if layer not in valid_layers:
                print(f"Unknown layer '{layer}'. Choose from: {', '.join(valid_layers)}")
                continue
            print(world.render_ascii_map(layer))

        elif cmd == "cut":
            if len(args) < 2:
                print("Usage: cut <x> <y> [target_cover]   (e.g., cut 5 5 0.15)")
                continue
            try:
                x, y = int(args[0]), int(args[1])
                target = float(args[2]) if len(args) >= 3 else 0.15
                ev = world.intervene_cut_forest(x, y, target)
                print(f"Intervention recorded: {ev['description']}")
            except ValueError:
                print("Error: Invalid coordinates or target coverage.")

        elif cmd == "status":
            s = world.get_world_summary()
            print(f"--- WORLD STATUS: Day {s['day']} ---")
            print(f"Avg Temperature:     {s['avg_temperature']} °C")
            print(f"Avg Rainfall:        {s['avg_rainfall']} mm")
            print(f"Avg Soil Moisture:   {s['avg_soil_moisture']}")
            print(f"Avg Soil Fertility:  {s['avg_soil_fertility']}")
            print(f"Avg Vegetation:      {s['avg_vegetation_cover'] * 100:.1f}%")
            print(f"Avg Daily Erosion:   {s['avg_erosion']} mm")
            print(f"Avg Daily Runoff:    {s['avg_runoff']} mm")
            print(f"Avg Topsoil Depth:   {s['avg_soil_depth']} m")

        elif cmd == "experiment":
            print("\nRunning Experiment 1: Deforestation comparison (Day 1-300)...")
            res = run_deforestation_experiment(seed=42)
            print_experiment_report(res)

        else:
            print(f"Unknown command: '{cmd}'. Type 'help' for valid commands.")


if __name__ == "__main__":
    run_cli()
