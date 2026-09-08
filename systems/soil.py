"""
Soil System for World Engine v0.1
Responsible for:
- Soil erosion from surface runoff and bare terrain
- Soil depth evolution (weathering generation vs erosive loss)
- Soil fertility dynamics (humus creation from biomass vs leaching/erosion loss)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artificial_civilization.world.world import World


class SoilSystem:
    def __init__(self):
        # Daily bedrock weathering into new soil (meters/day)
        self.weathering_rate_m = 0.00003
        # Baseline erodibility coefficient
        self.erodibility_coeff = 0.012

    def update(self, world: "World") -> None:
        """
        Advance soil dynamics by 1 day.
        Calculates runoff-induced erosion, topsoil depth loss, and organic fertility turnover.
        """
        for row in world.grid:
            for cell in row:
                veg = cell.vegetation_cover
                runoff = cell.runoff

                # 1. Soil Erosion
                # Bare soil has almost no root tensile strength or canopy umbrella protection.
                # Protective factor: roots bind soil; foliage dissipates raindrop energy.
                canopy_protection = veg ** 1.5  # Non-linear protective threshold
                exposure_factor = max(0.05, 1.0 - canopy_protection)
                
                # Kinetic energy of runoff (steeper elevation increases water velocity)
                slope_proxy = 0.8 + (cell.elevation / 600.0)
                
                # Daily erosion in mm of topsoil stripped
                daily_erosion = runoff * exposure_factor * slope_proxy * self.erodibility_coeff
                cell.erosion = daily_erosion

                # 2. Soil Depth Dynamics
                # Erosion removes topsoil (convert mm to meters)
                depth_loss_m = daily_erosion * 0.001
                # Underlying rock weathering gradually builds soil depth
                depth_gain_m = self.weathering_rate_m
                
                cell.soil_depth = max(0.05, cell.soil_depth - depth_loss_m + depth_gain_m)

                # 3. Soil Fertility Dynamics
                # Organic enrichment: leaves, roots, decaying organic matter
                biomass_turnover = 0.0010 * veg * min(1.0, cell.soil_moisture * 1.5)
                
                # Nutrient loss: severe erosion carries away nutrient-rich humus
                erosion_fertility_loss = daily_erosion * 0.03
                
                # Slow natural chemical leaching
                leaching_loss = 0.0001

                cell.soil_fertility = max(
                    0.05,
                    min(1.0, cell.soil_fertility + biomass_turnover - erosion_fertility_loss - leaching_loss)
                )

                cell.clamp_invariants()
