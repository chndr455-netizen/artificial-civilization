"""
Soil System for World Engine v0.2
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
        # Bedrock weathering rate: ~0.05 mm of new soil generated per year (~0.00000014 m/day)
        self.weathering_rate_m = 0.00000014
        # Calibrated erodibility coefficient for geological timescales (decades, not days)
        self.erodibility_coeff = 0.00035

    def update(self, world: "World") -> None:
        """
        Advance soil dynamics by 1 day.
        Calculates runoff-induced erosion, topsoil depth loss, and organic fertility turnover
        calibrated to natural multi-decade geological pacing.
        """
        for row in world.grid:
            for cell in row:
                veg = cell.vegetation_cover
                runoff = cell.runoff

                # 1. Soil Erosion (Geological pacing)
                # Dense forest canopy and deep root meshes reduce soil detachment by up to 99%.
                # Bare, cleared soil on slopes is vulnerable during heavy storm runoff.
                canopy_protection = veg ** 2.0
                exposure_factor = max(0.02, 1.0 - canopy_protection)
                
                # Kinetic energy depends on actual local terrain gradient.  A
                # high but flat plateau therefore does not behave like a steep
                # hillside merely because of its altitude.
                slope_factor = 1.0 + 25.0 * cell.slope
                erosive_water = cell.runoff + 0.25 * cell.flow_accumulation
                
                # Erosion in mm of topsoil stripped during this event
                # Intact forest loses ~0.00005 mm/storm; bare disturbed slope loses ~0.002 - 0.008 mm/storm
                daily_erosion = erosive_water * exposure_factor * slope_factor * self.erodibility_coeff
                cell.erosion = daily_erosion

                # 2. Soil Depth Dynamics (Meters)
                depth_loss_m = daily_erosion * 0.001
                depth_gain_m = self.weathering_rate_m
                cell.soil_depth = max(0.05, cell.soil_depth - depth_loss_m + depth_gain_m)

                # 3. Soil Fertility Dynamics
                # Slow organic enrichment from leaf litter and root decay
                biomass_turnover = 0.00025 * veg * min(1.0, cell.soil_moisture * 1.5)
                
                # Erosive nutrient removal
                erosion_fertility_loss = daily_erosion * 0.15
                
                # Natural chemical leaching
                leaching_loss = 0.00002

                cell.soil_fertility = max(
                    0.05,
                    min(1.0, cell.soil_fertility + biomass_turnover - erosion_fertility_loss - leaching_loss)
                )

                cell.clamp_invariants()
