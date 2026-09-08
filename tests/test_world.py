"""
Unit Tests for World Engine v0.1
Validates invariants, causal relationships, determinism, and conservation rules.
"""

import unittest
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


if __name__ == "__main__":
    unittest.main()
