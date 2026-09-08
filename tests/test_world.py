"""
Unit Tests for World Engine v0.1
Validates invariants, causal relationships, determinism, and conservation rules.
"""

import os
import sys
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_TESTS_DIR)
_PARENT_DIR = os.path.dirname(_PROJECT_DIR)
for _p in (_PROJECT_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from world.world import World
    from experiments.deforestation import run_deforestation_experiment
except ImportError:
    from artificial_civilization.world.world import World
    from artificial_civilization.experiments.deforestation import run_deforestation_experiment


class TestWorldEngine(unittest.TestCase):
    def test_world_initialization(self):
        """World should initialize with 10x10 cells and valid terrain."""
        world = World(width=10, height=10, seed=123)
        self.assertEqual(len(world.grid), 10)
        self.assertEqual(len(world.grid[0]), 10)
        self.assertEqual(world.day, 1)

        cell = world.get_cell(5, 5)
        self.assertIsNotNone(cell)
        self.assertTrue(40.0 <= cell.elevation <= 500.0)
        self.assertTrue(0.0 <= cell.soil_moisture <= 1.0)
        self.assertTrue(0.0 <= cell.vegetation_cover <= 1.0)
        self.assertTrue(0.0 <= cell.soil_fertility <= 1.0)

    def test_determinism_and_random_seed(self):
        """Identical random seeds must produce identical simulation trajectories."""
        world_a = World(width=10, height=10, seed=777)
        world_b = World(width=10, height=10, seed=777)

        world_a.tick(15)
        world_b.tick(15)

        for y in range(10):
            for x in range(10):
                ca = world_a.get_cell(x, y)
                cb = world_b.get_cell(x, y)
                self.assertAlmostEqual(ca.temperature, cb.temperature, places=5)
                self.assertAlmostEqual(ca.rainfall, cb.rainfall, places=5)
                self.assertAlmostEqual(ca.soil_moisture, cb.soil_moisture, places=5)
                self.assertAlmostEqual(ca.vegetation_cover, cb.vegetation_cover, places=5)
                self.assertAlmostEqual(ca.erosion, cb.erosion, places=5)

    def test_conservation_and_physical_bounds(self):
        """Ensure no impossible states occur across 365 daily simulation ticks."""
        world = World(width=10, height=10, seed=999)
        world.tick(365)

        self.assertEqual(world.day, 366)
        for row in world.grid:
            for cell in row:
                self.assertTrue(0.0 <= cell.soil_moisture <= 1.0, f"Moisture invalid: {cell.soil_moisture}")
                self.assertTrue(0.0 <= cell.soil_fertility <= 1.0, f"Fertility invalid: {cell.soil_fertility}")
                self.assertTrue(0.0 <= cell.vegetation_cover <= 1.0, f"Cover invalid: {cell.vegetation_cover}")
                self.assertTrue(cell.soil_depth >= 0.05, f"Soil depth negative or zero: {cell.soil_depth}")
                self.assertTrue(cell.rainfall >= 0.0, f"Negative rainfall: {cell.rainfall}")
                self.assertTrue(cell.runoff >= 0.0, f"Negative runoff: {cell.runoff}")
                self.assertTrue(cell.erosion >= 0.0, f"Negative erosion: {cell.erosion}")

    def test_cell_inspection_formatting(self):
        """Inspect command format must match blueprint Section 14."""
        world = World(width=10, height=10, seed=123)
        world.tick(5)
        output = world.inspect(5, 5)

        self.assertIn("Cell (5,5)", output)
        self.assertIn("Elevation:", output)
        self.assertIn("Temperature:", output)
        self.assertIn("Rainfall:", output)
        self.assertIn("Soil Moisture:", output)
        self.assertIn("Soil Fertility:", output)
        self.assertIn("Erosion:", output)
        self.assertIn("Forest Cover:", output)

    def test_deforestation_causal_consequence(self):
        """Deforested cell must experience increased runoff and erosion compared to control."""
        res = run_deforestation_experiment(seed=42, intervention_day=50, total_days=150)
        # World B with cut forest should experience more cumulative runoff and erosion
        self.assertGreater(res["total_runoff_b"], res["total_runoff_a"])
        self.assertGreater(res["total_erosion_b"], res["total_erosion_a"])

    def test_slope_comes_from_neighbors_not_absolute_elevation(self):
        """A flat high cell has zero slope; a low steep cell does not."""
        world = World(width=3, height=1, seed=1, cell_size_m=100.0)
        world.get_cell(0, 0).elevation = 400.0
        world.get_cell(1, 0).elevation = 400.0
        world.get_cell(2, 0).elevation = 50.0
        world._update_slopes()

        self.assertEqual(world.get_cell(0, 0).slope, 0.0)
        self.assertAlmostEqual(world.get_cell(1, 0).slope, 3.5)
        self.assertEqual(world.get_cell(2, 0).slope, 0.0)

    def test_surface_water_moves_downhill_between_cells(self):
        """Routing moves water into a lower neighbor, independent of grid order."""
        world = World(width=2, height=1, seed=1, cell_size_m=100.0)
        high = world.get_cell(0, 0)
        low = world.get_cell(1, 0)
        high.elevation, low.elevation = 200.0, 100.0
        high.soil_moisture = low.soil_moisture = 1.0
        high.surface_water, low.surface_water = 10.0, 0.0
        high.rainfall = low.rainfall = 0.0
        high.temperature = low.temperature = -5.0
        world._update_slopes()

        world.water_system.update(world)

        self.assertLess(high.surface_water, 10.0)
        self.assertGreater(low.surface_water, 0.0)
        self.assertGreater(high.flow_accumulation, 0.0)

    def test_water_balance_is_conserved_after_rain_and_routing(self):
        """Rain, storage, and evapotranspiration must balance each daily tick."""
        world = World(width=4, height=4, seed=123)
        world.tick(40)
        self.assertAlmostEqual(world.last_water_balance["residual_mm"], 0.0, places=8)


if __name__ == "__main__":
    unittest.main()
