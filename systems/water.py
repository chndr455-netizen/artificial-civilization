"""
Water / Hydrology System for World Engine v0.2
Responsible for:
- Rainfall infiltration into the soil layer
- Soil storage, surface runoff generation, and downhill routing
- Evaporation and plant transpiration (evapotranspiration)
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artificial_civilization.world.world import World


class WaterSystem:
    def __init__(self):
        # Base daily evapotranspiration rate at 20°C (scaled for natural multi-week retention)
        self.base_evap_rate = 0.018
        # Deep soil water holding capacity factor (mm of water per 1.0 soil moisture unit)
        self.soil_sponge_factor = 45.0
        # At this fraction of available surface water, a slope of 1.0 would
        # route 90% in one day.  The cap keeps a small local water store.
        self.flow_rate = 0.90

    def update(self, world: "World") -> None:
        """
        Advance hydrology by 1 day.
        Calculates a local water balance, then routes surface water using a
        two-phase update.  Every cell proposes an outflow from the same frozen
        state before any transfer is applied, so iteration order cannot change
        the result.
        """
        initial_storage = sum(
            self._soil_water_mm(cell) + cell.surface_water
            for row in world.grid
            for cell in row
        )
        rainfall_input = 0.0
        evapotranspiration = 0.0

        # Phase 1: rainfall, infiltration, and evapotranspiration are local.
        for row in world.grid:
            for cell in row:
                rain = cell.rainfall
                veg = cell.vegetation_cover
                rainfall_input += rain

                # Dense root systems improve soil absorption.  Storage capacity
                # is based on actual remaining pore space; excess stays at the
                # surface instead of disappearing at the 0..1 moisture bound.
                current_soil_water = self._soil_water_mm(cell)
                soil_capacity = self._soil_capacity_mm(cell)
                storage_headroom = max(0.0, soil_capacity - current_soil_water)
                veg_enhancement = 0.4 + 0.6 * veg  # roots create porous channels
                depth_factor = min(1.5, cell.soil_depth / 1.0)

                max_infiltration_mm = min(
                    storage_headroom,
                    20.0 * veg_enhancement * depth_factor,
                )
                available_water = rain + cell.surface_water
                infiltrated_mm = min(available_water, max_infiltration_mm)
                cell.surface_water = available_water - infiltrated_mm
                cell.runoff = max(0.0, rain - infiltrated_mm)
                current_soil_water += infiltrated_mm

                # Evapotranspiration is a real output from soil storage.
                temp_factor = max(0.0, (cell.temperature + 5.0) / 25.0)
                soil_evap = self.base_evap_rate * (1.0 - 0.5 * veg) * cell.soil_moisture * temp_factor
                transpiration = self.base_evap_rate * 0.8 * veg * cell.soil_moisture * temp_factor
                total_loss_mm = min(current_soil_water, (soil_evap + transpiration) * soil_capacity)
                current_soil_water -= total_loss_mm
                evapotranspiration += total_loss_mm
                cell.soil_moisture = current_soil_water / soil_capacity

                cell.clamp_invariants()

        # Phase 2: calculate all downhill transfers from the same post-rain,
        # pre-routing snapshot.  Water reaching a neighbor is available to move
        # on the following day, providing a stable daily timestep.
        transfers = []
        throughflow = {}
        external_outflow = 0.0
        for row in world.grid:
            for cell in row:
                downhill = world.downhill_neighbors(cell)
                available = cell.surface_water
                if not downhill or available <= 0.0:
                    # A basin retains water, but an edge cell without a lower
                    # in-world neighbor represents a watershed outlet.  Its
                    # exported water is included in the daily balance below.
                    if available > 0.0 and self._is_world_edge(cell, world):
                        outlet_flow = available * self.flow_rate
                        cell.surface_water -= outlet_flow
                        external_outflow += outlet_flow
                        throughflow[(cell.x, cell.y)] = outlet_flow
                    else:
                        throughflow[(cell.x, cell.y)] = 0.0
                    continue

                steepest_gradient = max(gradient for _, gradient in downhill)
                targets = [neighbor for neighbor, gradient in downhill if abs(gradient - steepest_gradient) < 1e-12]
                outflow = min(available, available * min(self.flow_rate, steepest_gradient * self.flow_rate))
                throughflow[(cell.x, cell.y)] = outflow
                share = outflow / len(targets)
                for target in targets:
                    transfers.append((cell, target, share))

        incoming = {(cell.x, cell.y): 0.0 for row in world.grid for cell in row}
        outgoing = {(cell.x, cell.y): 0.0 for row in world.grid for cell in row}
        for source, target, amount in transfers:
            outgoing[(source.x, source.y)] += amount
            incoming[(target.x, target.y)] += amount

        for row in world.grid:
            for cell in row:
                key = (cell.x, cell.y)
                cell.surface_water += incoming[key] - outgoing[key]
                # A short memory makes channels visible through repeated storm
                # flow while preserving the underlying numerical state.
                cell.flow_accumulation = 0.50 * cell.flow_accumulation + 0.50 * (
                    cell.runoff + incoming[key] + throughflow[key]
                )
                cell.clamp_invariants()

        final_storage = sum(
            self._soil_water_mm(cell) + cell.surface_water
            for row in world.grid
            for cell in row
        )
        world.last_water_balance = {
            "initial_storage_mm": initial_storage,
            "rainfall_input_mm": rainfall_input,
            "evapotranspiration_mm": evapotranspiration,
            "external_outflow_mm": external_outflow,
            "final_storage_mm": final_storage,
            "residual_mm": initial_storage + rainfall_input - evapotranspiration - external_outflow - final_storage,
        }

    def _soil_capacity_mm(self, cell) -> float:
        """Water capacity of this cell's active soil layer in millimetres."""
        return self.soil_sponge_factor * max(0.01, cell.soil_depth)

    def _soil_water_mm(self, cell) -> float:
        return cell.soil_moisture * self._soil_capacity_mm(cell)

    @staticmethod
    def _is_world_edge(cell, world: "World") -> bool:
        return cell.x in (0, world.width - 1) or cell.y in (0, world.height - 1)
