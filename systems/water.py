"""
Water / Hydrology System for World Engine v0.1
Responsible for:
- Rainfall infiltration into the soil layer
- Canopy interception and surface runoff generation
- Evaporation and plant transpiration (evapotranspiration)
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artificial_civilization.world.world import World


class WaterSystem:
    def __init__(self):
        # Base daily evaporation rate at 20°C
        self.base_evap_rate = 0.04
        # Water holding capacity factor
        self.soil_sponge_factor = 25.0  # mm of water per 0.1 soil moisture unit

    def update(self, world: "World") -> None:
        """
        Advance hydrology by 1 day.
        Calculates infiltration, runoff, and evapotranspiration.
        """
        for row in world.grid:
            for cell in row:
                rain = cell.rainfall
                veg = cell.vegetation_cover
                current_moisture = cell.soil_moisture

                # 1. Infiltration Capacity
                # Dense root systems and vegetation canopy improve soil absorption.
                # Saturated soil (high moisture) rejects water.
                saturation_headroom = max(0.05, 1.0 - current_moisture)
                veg_enhancement = 0.4 + 0.6 * veg  # roots create porous channels
                depth_factor = min(1.5, cell.soil_depth / 1.0)
                
                # Maximum millimeters of water soil can absorb this tick
                max_infiltration_mm = 20.0 * saturation_headroom * veg_enhancement * depth_factor

                # 2. Infiltration & Runoff
                if rain > 0:
                    infiltrated_mm = min(rain, max_infiltration_mm)
                    # Excess rain becomes surface runoff
                    cell.runoff = max(0.0, rain - infiltrated_mm)
                    
                    # Convert infiltrated water to soil moisture increase
                    moisture_gain = infiltrated_mm / self.soil_sponge_factor
                    cell.soil_moisture = min(1.0, current_moisture + moisture_gain)
                else:
                    cell.runoff = 0.0

                # 3. Evapotranspiration (soil evaporation + vegetation transpiration)
                temp_factor = max(0.0, (cell.temperature + 5.0) / 25.0)
                
                # Direct surface evaporation (higher on bare wet soil)
                soil_evap = self.base_evap_rate * (1.0 - 0.5 * veg) * cell.soil_moisture * temp_factor
                
                # Plant transpiration (transpires water as it metabolizes)
                transpiration = self.base_evap_rate * 0.8 * veg * cell.soil_moisture * temp_factor
                
                total_loss = soil_evap + transpiration
                cell.soil_moisture = max(0.0, cell.soil_moisture - total_loss)

                cell.clamp_invariants()
