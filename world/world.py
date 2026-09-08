"""
Authoritative World State & Simulation Engine for World Engine v0.1
Maintains canonical 10x10 spatial world state and runs sequential natural systems.
"""

import math
import random
from typing import List, Dict, Any, Optional, Tuple

from artificial_civilization.world.cell import Cell
from artificial_civilization.systems.weather import WeatherSystem
from artificial_civilization.systems.water import WaterSystem
from artificial_civilization.systems.soil import SoilSystem
from artificial_civilization.systems.vegetation import VegetationSystem


class World:
    def __init__(self, width: int = 10, height: int = 10, seed: int = 12345):
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = random.Random(seed)
        self.day = 1

        # Instantiate modular natural systems
        self.weather_system = WeatherSystem()
        self.water_system = WaterSystem()
        self.soil_system = SoilSystem()
        self.vegetation_system = VegetationSystem()

        # Log of events (human interventions, natural anomalies)
        self.event_log: List[Dict[str, Any]] = []

        # Initialize the 2D spatial grid (10 x 10 cells)
        self.grid: List[List[Cell]] = self._generate_terrain()

    def _generate_terrain(self) -> List[List[Cell]]:
        """
        Procedurally initialize 10x10 terrain cells with coherent elevation gradients
        (mountain ridge to coastal lowland) and initial natural states.
        """
        grid: List[List[Cell]] = []
        for y in range(self.height):
            row: List[Cell] = []
            for x in range(self.width):
                # Elevation gradient: higher inland/north-west (up to ~450m), sloping to lowlands (~60m)
                norm_x = x / max(1, self.width - 1)
                norm_y = y / max(1, self.height - 1)
                
                # Smooth base gradient + procedural undulating hills
                gradient = (1.0 - norm_x * 0.6) * (1.0 - norm_y * 0.4)
                hill_undulation = (
                    math.sin(norm_x * math.pi * 2.0) * 40.0 +
                    math.cos(norm_y * math.pi * 2.0) * 35.0
                )
                elevation = max(40.0, 80.0 + gradient * 320.0 + hill_undulation + self.rng.uniform(-10.0, 10.0))

                cell = Cell(
                    x=x,
                    y=y,
                    elevation=elevation,
                    temperature=20.0,
                    rainfall=0.0,
                    soil_moisture=0.55 + self.rng.uniform(-0.05, 0.05),
                    soil_depth=1.1 + self.rng.uniform(-0.1, 0.1),
                    soil_fertility=0.72 + self.rng.uniform(-0.05, 0.05),
                    erosion=0.0,
                    vegetation_cover=0.75 + self.rng.uniform(-0.05, 0.05),
                )
                cell.clamp_invariants()
                row.append(cell)
            grid.append(row)
        return grid

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Safely fetch a cell by (x, y) coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def tick(self, days: int = 1) -> None:
        """
        Advance the simulation clock by specified number of days (default 1).
        Executes systems in strict causal order (Section 2, Principle 5):
        Weather -> Water -> Soil -> Vegetation.
        """
        for _ in range(days):
            self.weather_system.update(self)
            self.water_system.update(self)
            self.soil_system.update(self)
            self.vegetation_system.update(self)
            self.day += 1

    def inspect(self, x: int, y: int) -> str:
        """
        Format individual cell inspection matching Section 14 of blueprint:
        Cell (5,5)

        Elevation:       182 m
        Temperature:      27.4°C
        Rainfall:          8.2 mm
        Soil Moisture:    0.54
        Soil Fertility:   0.68
        Erosion:           0.03
        Forest Cover:      0.72
        """
        cell = self.get_cell(x, y)
        if not cell:
            return f"Error: Cell ({x},{y}) out of bounds (0-{self.width-1}, 0-{self.height-1})."

        lines = [
            f"Cell ({cell.x},{cell.y})",
            "",
            f"Elevation:       {cell.elevation:>6.1f} m",
            f"Temperature:     {cell.temperature:>6.1f}°C",
            f"Rainfall:        {cell.rainfall:>6.1f} mm",
            f"Soil Moisture:   {cell.soil_moisture:>6.2f}",
            f"Soil Fertility:  {cell.soil_fertility:>6.2f}",
            f"Soil Depth:      {cell.soil_depth:>6.2f} m",
            f"Runoff:          {cell.runoff:>6.1f} mm",
            f"Erosion:         {cell.erosion:>6.4f} mm",
            f"Forest Cover:    {cell.vegetation_cover:>6.2f}",
        ]
        return "\n".join(lines)

    def intervene_cut_forest(self, x: int, y: int, target_cover: float = 0.15) -> Dict[str, Any]:
        """
        Controlled human intervention: clear forest coverage at (x, y) to target_cover.
        (Section 8 & Section 20 of blueprint).
        """
        cell = self.get_cell(x, y)
        if not cell:
            raise ValueError(f"Cell ({x},{y}) out of bounds")

        old_cover = cell.vegetation_cover
        cell.vegetation_cover = max(0.0, min(1.0, target_cover))
        cell.clamp_invariants()

        event = {
            "day": self.day,
            "type": "TREE_CUTTING",
            "x": x,
            "y": y,
            "old_cover": round(old_cover, 2),
            "new_cover": round(cell.vegetation_cover, 2),
            "description": f"Forest at ({x},{y}) cleared from {old_cover*100:.0f}% to {cell.vegetation_cover*100:.0f}%",
        }
        self.event_log.append(event)
        return event

    def get_world_summary(self) -> Dict[str, float]:
        """Calculate average environmental metrics across all 100 cells."""
        total = self.width * self.height
        avg_temp = sum(c.temperature for row in self.grid for c in row) / total
        avg_rain = sum(c.rainfall for row in self.grid for c in row) / total
        avg_moist = sum(c.soil_moisture for row in self.grid for c in row) / total
        avg_fert = sum(c.soil_fertility for row in self.grid for c in row) / total
        avg_veg = sum(c.vegetation_cover for row in self.grid for c in row) / total
        avg_erosion = sum(c.erosion for row in self.grid for c in row) / total
        avg_runoff = sum(c.runoff for row in self.grid for c in row) / total
        avg_depth = sum(c.soil_depth for row in self.grid for c in row) / total

        return {
            "day": self.day,
            "avg_temperature": round(avg_temp, 2),
            "avg_rainfall": round(avg_rain, 2),
            "avg_soil_moisture": round(avg_moist, 3),
            "avg_soil_fertility": round(avg_fert, 3),
            "avg_vegetation_cover": round(avg_veg, 3),
            "avg_erosion": round(avg_erosion, 4),
            "avg_runoff": round(avg_runoff, 2),
            "avg_soil_depth": round(avg_depth, 3),
        }

    def render_ascii_map(self, layer: str = "vegetation") -> str:
        """
        v0.2 ASCII / grid representation (Section 15 of blueprint).
        Layers: 'vegetation', 'moisture', 'erosion', 'elevation', 'fertility'
        """
        chars_veg = [" ", "░", "▒", "▓", "█"]
        chars_moist = [".", "-", "~", "=", "≈"]
        chars_elev = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

        header = f"--- [Day {self.day}] ASCII Map: {layer.upper()} ---"
        col_numbers = "   " + " ".join(f"{x}" for x in range(self.width))
        lines = [header, col_numbers, "  +" + "--" * self.width + "+"]

        for y in range(self.height):
            row_str = f"{y:2d}|"
            for x in range(self.width):
                cell = self.grid[y][x]
                if layer == "vegetation":
                    idx = int(cell.vegetation_cover * (len(chars_veg) - 1))
                    char = chars_veg[min(len(chars_veg) - 1, max(0, idx))]
                elif layer == "moisture":
                    idx = int(cell.soil_moisture * (len(chars_moist) - 1))
                    char = chars_moist[min(len(chars_moist) - 1, max(0, idx))]
                elif layer == "fertility":
                    idx = int(cell.soil_fertility * (len(chars_veg) - 1))
                    char = chars_veg[min(len(chars_veg) - 1, max(0, idx))]
                elif layer == "erosion":
                    if cell.erosion < 0.005:
                        char = "."
                    elif cell.erosion < 0.02:
                        char = "x"
                    else:
                        char = "X"
                elif layer == "elevation":
                    norm_e = (cell.elevation - 40.0) / 400.0
                    idx = int(norm_e * (len(chars_elev) - 1))
                    char = chars_elev[min(len(chars_elev) - 1, max(0, idx))]
                else:
                    char = "?"
                row_str += f" {char}"
            row_str += " |"
            lines.append(row_str)

        lines.append("  +" + "--" * self.width + "+")
        return "\n".join(lines)
