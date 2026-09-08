"""
Vegetation System for World Engine v0.1
Responsible for:
- Plant growth dynamics influenced by temperature, moisture, fertility, and soil depth
- Environmental stress and mortality (drought, frost, natural senescence)
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artificial_civilization.world.world import World


class VegetationSystem:
    def __init__(self):
        # Maximum daily vegetative growth rate (calibrated for seasonal biological inertia)
        self.base_growth_rate = 0.0035
        # Background natural turnover / senescence
        self.natural_decay_rate = 0.0004

    def update(self, world: "World") -> None:
        """
        Advance vegetation growth and decay by 1 day.
        Calculates biomass change based on ecological factors.
        """
        for row in world.grid:
            for cell in row:
                temp = cell.temperature
                moisture = cell.soil_moisture
                fertility = cell.soil_fertility
                depth = cell.soil_depth
                veg = cell.vegetation_cover

                # 1. Temperature Suitability (0.0 to 1.0)
                # Optimal between 18°C and 26°C; slows below 10°C; stops below 3°C
                if temp <= 3.0:
                    temp_factor = 0.0
                elif temp < 20.0:
                    temp_factor = (temp - 3.0) / 17.0
                elif temp <= 28.0:
                    temp_factor = 1.0
                elif temp < 42.0:
                    temp_factor = (42.0 - temp) / 14.0
                else:
                    temp_factor = 0.0

                # 2. Moisture Suitability (0.0 to 1.0)
                # Ideal range: 0.35 to 0.75. Wilting point < 0.15. Saturated > 0.90 causes root hypoxia.
                if moisture < 0.12:
                    moisture_factor = 0.0
                elif moisture < 0.40:
                    moisture_factor = (moisture - 0.12) / 0.28
                elif moisture <= 0.75:
                    moisture_factor = 1.0
                else:
                    moisture_factor = max(0.2, 1.0 - (moisture - 0.75) * 3.0)

                # 3. Soil Depth & Fertility Factor
                depth_factor = min(1.0, depth / 0.6)  # at least 0.6m for full canopy root support
                soil_support = fertility * depth_factor

                # 4. Growth (Logistic carrying capacity)
                # Available canopy room: (1.0 - veg)
                carrying_headroom = max(0.0, 1.0 - veg)
                daily_growth = self.base_growth_rate * temp_factor * moisture_factor * soil_support * carrying_headroom

                # 5. Decay and Environmental Stress
                stress_decay = self.natural_decay_rate
                
                # Severe drought stress
                if moisture < 0.15:
                    stress_decay += 0.02 * (1.0 - moisture / 0.15)
                
                # Frost damage
                if temp < 0.0:
                    stress_decay += 0.015 * min(1.0, abs(temp) / 5.0)

                # Apply net daily change
                new_veg = veg + daily_growth - stress_decay
                cell.vegetation_cover = max(0.0, min(1.0, new_veg))

                cell.clamp_invariants()
