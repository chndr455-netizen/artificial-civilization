"""
Authoritative World State & Simulation Engine for World Engine v0.2.
Maintains canonical spatial world state and runs deterministic natural systems.
"""

import math
import random
from typing import List, Dict, Any, Optional, Tuple

try:
    from world.cell import Cell
    from systems.weather import WeatherSystem
    from systems.water import WaterSystem
    from systems.soil import SoilSystem
    from systems.vegetation import VegetationSystem
except ImportError:
    from artificial_civilization.world.cell import Cell
    from artificial_civilization.systems.weather import WeatherSystem
    from artificial_civilization.systems.water import WaterSystem
    from artificial_civilization.systems.soil import SoilSystem
    from artificial_civilization.systems.vegetation import VegetationSystem


class World:
    RIVER_FLOW_THRESHOLD = 50.0  # mm/day, calibrated for the 100 m v0.2 grid
    HIGH_FLOW_EVENT_THRESHOLD = 100.0
    HIGH_EROSION_EVENT_THRESHOLD = 0.05
    DROUGHT_EVENT_THRESHOLD = 0.15

    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        seed: int = 88888,
        cell_size_m: float = 100.0,
    ):
        self.width = width
        self.height = height
        self.seed = seed
        self.cell_size_m = cell_size_m
        self.rng = random.Random(seed)
        self.day = 1

        # Instantiate modular natural systems
        self.weather_system = WeatherSystem()
        self.water_system = WaterSystem()
        self.soil_system = SoilSystem()
        self.vegetation_system = VegetationSystem()

        # Log of events (human interventions, natural anomalies)
        self.event_log: List[Dict[str, Any]] = []
        self.annual_summaries: List[Dict[str, Any]] = []
        self._active_natural_events = set()
        self._annual_natural_event_keys = set()

        # Initialize the 2D spatial grid (10 x 10 cells)
        self.grid: List[List[Cell]] = self._generate_terrain()
        self._update_slopes()

        # A diagnostic produced by WaterSystem each tick.  It lets tests and
        # experiments verify water accounting rather than only numeric bounds.
        self.last_water_balance: Dict[str, float] = {}
        self._year_start_state = self._snapshot_world_state()
        self._year_outflow_mm = 0.0
        self._year_peak_flow = {"value": 0.0, "x": 0, "y": 0, "day": self.day}

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

    def cardinal_neighbors(self, x: int, y: int) -> List[Cell]:
        """Return valid north, east, south, and west neighbors in fixed order."""
        neighbors: List[Cell] = []
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbor = self.get_cell(x + dx, y + dy)
            if neighbor is not None:
                neighbors.append(neighbor)
        return neighbors

    def downhill_neighbors(self, cell: Cell) -> List[Tuple[Cell, float]]:
        """Return lower cardinal neighbors with their terrain gradient.

        Gradients are derived from elevation differences, not a cell's absolute
        elevation.  This is the v0.2 spatial relationship used by routing and
        erosion.
        """
        downhill: List[Tuple[Cell, float]] = []
        for neighbor in self.cardinal_neighbors(cell.x, cell.y):
            drop_m = cell.elevation - neighbor.elevation
            if drop_m > 0.0:
                downhill.append((neighbor, drop_m / self.cell_size_m))
        return downhill

    def _update_slopes(self) -> None:
        """Cache each cell's steepest cardinal downhill terrain gradient."""
        for row in self.grid:
            for cell in row:
                downhill = self.downhill_neighbors(cell)
                cell.slope = max((gradient for _, gradient in downhill), default=0.0)

    def tick(self, days: int = 1) -> None:
        """
        Advance the simulation clock by specified number of days (default 1).
        Executes systems in strict causal order:
        Weather -> local water balance and routing -> Soil -> Vegetation.
        """
        for _ in range(days):
            self.weather_system.update(self)
            self.water_system.update(self)
            self.soil_system.update(self)
            self.vegetation_system.update(self)
            self._record_natural_events()
            self._accumulate_yearly_observations()
            self.day += 1
            if (self.day - 1) % 365 == 0:
                self._finalize_year((self.day - 1) // 365)

    def _snapshot_world_state(self) -> Dict[str, float]:
        """Capture the small, stable set of values used in annual comparisons."""
        summary = self.get_world_summary()
        return {
            "avg_vegetation_cover": summary["avg_vegetation_cover"],
            "avg_soil_moisture": summary["avg_soil_moisture"],
            "avg_soil_fertility": summary["avg_soil_fertility"],
            "avg_soil_depth": summary["avg_soil_depth"],
        }

    def _record_natural_events(self) -> None:
        """Record threshold crossings, not repetitive daily status messages."""
        for row in self.grid:
            for cell in row:
                self._record_threshold_event(
                    "HIGH_FLOW",
                    cell.flow_accumulation >= self.HIGH_FLOW_EVENT_THRESHOLD,
                    cell,
                    f"Routed flow reached {cell.flow_accumulation:.1f} mm/day",
                )
                self._record_threshold_event(
                    "HIGH_EROSION",
                    cell.erosion >= self.HIGH_EROSION_EVENT_THRESHOLD,
                    cell,
                    f"Soil erosion reached {cell.erosion:.4f} mm/day",
                )
                self._record_threshold_event(
                    "DROUGHT",
                    cell.soil_moisture <= self.DROUGHT_EVENT_THRESHOLD,
                    cell,
                    f"Soil moisture fell to {cell.soil_moisture:.2f}",
                )

    def _record_threshold_event(self, event_type: str, active: bool, cell: Cell, description: str) -> None:
        key = (event_type, cell.x, cell.y)
        if active and key not in self._active_natural_events:
            self._active_natural_events.add(key)
            year = (self.day - 1) // 365 + 1
            annual_key = (year, event_type, cell.x, cell.y)
            if annual_key not in self._annual_natural_event_keys:
                self._annual_natural_event_keys.add(annual_key)
                self.event_log.append({
                    "day": self.day,
                    "type": event_type,
                    "x": cell.x,
                    "y": cell.y,
                    "description": description,
                })
        elif not active:
            self._active_natural_events.discard(key)

    def _accumulate_yearly_observations(self) -> None:
        self._year_outflow_mm += self.last_water_balance.get("external_outflow_mm", 0.0)
        peak = max((cell for row in self.grid for cell in row), key=lambda cell: cell.flow_accumulation)
        if peak.flow_accumulation > self._year_peak_flow["value"]:
            self._year_peak_flow = {
                "value": peak.flow_accumulation,
                "x": peak.x,
                "y": peak.y,
                "day": self.day,
            }

    def _finalize_year(self, year: int) -> None:
        start_day = (year - 1) * 365 + 1
        end_day = year * 365
        yearly_events = [
            dict(event)
            for event in self.event_log
            if start_day <= event["day"] <= end_day
        ]
        self.annual_summaries.append({
            "year": year,
            "start_day": start_day,
            "end_day": end_day,
            "start_state": dict(self._year_start_state),
            "end_state": self._snapshot_world_state(),
            "events": yearly_events,
            "watershed_outflow_mm": self._year_outflow_mm,
            "peak_flow": dict(self._year_peak_flow),
        })
        self._year_start_state = self._snapshot_world_state()
        self._year_outflow_mm = 0.0
        self._year_peak_flow = {"value": 0.0, "x": 0, "y": 0, "day": self.day}

    def format_annual_summaries(self, year: Optional[int] = None) -> str:
        """Render completed-year history; the active year is intentionally omitted."""
        summaries = self.annual_summaries
        if year is not None:
            summaries = [summary for summary in summaries if summary["year"] == year]

        if not summaries:
            if year is not None:
                return f"No completed summary for Year {year}."
            current_year = (self.day - 1) // 365 + 1
            return (
                f"No completed year yet. Current simulation: Day {self.day}, "
                f"Year {current_year}."
            )

        sections = []
        for summary in summaries:
            start = summary["start_state"]
            end = summary["end_state"]
            lines = [
                f"[Year {summary['year']} Summary — Days {summary['start_day']}–{summary['end_day']}]",
                "",
                "Major events",
            ]
            if summary["events"]:
                # Interventions are deliberate historical actions, so always
                # show them.  Natural threshold crossings are kept in the raw
                # log but summarized to one representative event per type;
                # otherwise a stormy year would become unreadable.
                interventions = [event for event in summary["events"] if event["type"] == "TREE_CUTTING"]
                natural_representatives = {}
                for event in summary["events"]:
                    if event["type"] != "TREE_CUTTING":
                        natural_representatives.setdefault(event["type"], event)
                displayed_events = interventions + list(natural_representatives.values())
                displayed_events.sort(key=lambda event: event["day"])
                for event in displayed_events:
                    lines.append(
                        f"Day {event['day']} — {event['type']} at ({event['x']},{event['y']}): "
                        f"{event['description']}."
                    )
                remaining = len(summary["events"]) - len(displayed_events)
                if remaining > 0:
                    lines.append(f"… plus {remaining} additional threshold crossings retained in the event log.")
            else:
                lines.append("No major events were recorded.")

            peak = summary["peak_flow"]
            lines.extend([
                "",
                "Annual world changes",
                f"Average vegetation: {start['avg_vegetation_cover'] * 100:.1f}% → {end['avg_vegetation_cover'] * 100:.1f}%",
                f"Average soil moisture: {start['avg_soil_moisture']:.3f} → {end['avg_soil_moisture']:.3f}",
                f"Average soil fertility: {start['avg_soil_fertility']:.3f} → {end['avg_soil_fertility']:.3f}",
                f"Watershed outflow: {summary['watershed_outflow_mm']:.1f} cell-mm",
                f"Peak routed flow: {peak['value']:.1f} mm/day at ({peak['x']},{peak['y']}) on Day {peak['day']}",
            ])
            sections.append("\n".join(lines))
        return "\n\n".join(sections)

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
            f"Surface Water:   {cell.surface_water:>6.2f} mm",
            f"Flow Accum.:     {cell.flow_accumulation:>6.2f} mm/day",
            f"Terrain Slope:   {cell.slope:>6.3f}",
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
        avg_flow = sum(c.flow_accumulation for row in self.grid for c in row) / total

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
            "avg_flow_accumulation": round(avg_flow, 3),
        }

    def render_ascii_map(self, layer: str = "vegetation") -> str:
        """
        v0.2 ASCII / grid representation (Section 15 of blueprint).
        Layers: 'satellite', 'vegetation', 'moisture', 'erosion', 'elevation',
        'fertility', 'flow', and 'slope'.
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
                if layer == "satellite":
                    if cell.elevation >= 320.0:
                        char = "▲"  # Alpine Mountain Peak
                    elif cell.elevation >= 220.0 and cell.vegetation_cover < 0.45:
                        char = "⋀"  # Highland Rocky Ridge
                    elif cell.flow_accumulation >= self.RIVER_FLOW_THRESHOLD:
                        char = "~"  # Routed river channel / wetland basin
                    elif cell.vegetation_cover >= 0.68:
                        char = "♠"  # Dense Forest
                    elif cell.vegetation_cover >= 0.40:
                        char = "♣"  # Woodland / Grove
                    elif cell.vegetation_cover >= 0.18:
                        char = "*"  # Bushes / Shrubland
                    elif cell.vegetation_cover >= 0.08:
                        char = "."  # Grassland / Meadow
                    else:
                        char = "░"  # Bare / Cleared Earth
                elif layer == "vegetation":
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
                elif layer == "flow":
                    char = "~" if cell.flow_accumulation >= self.RIVER_FLOW_THRESHOLD else "."
                elif layer == "slope":
                    char = "^" if cell.slope >= 0.5 else "/" if cell.slope >= 0.15 else "."
                else:
                    char = "?"
                row_str += f" {char}"
            row_str += " |"
            lines.append(row_str)

        lines.append("  +" + "--" * self.width + "+")
        return "\n".join(lines)
