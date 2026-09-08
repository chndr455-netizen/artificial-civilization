"""
Cell Data Structure for World Engine v0.1
Represents a discrete spatial geographical cell in the simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Cell:
    x: int
    y: int
    elevation: float  # meters (e.g. 50 - 500m)

    # Weather & Atmosphere
    temperature: float = 20.0  # Celsius (°C)
    rainfall: float = 0.0      # mm per day

    # Hydrology
    soil_moisture: float = 0.5  # 0.0 (bone dry) to 1.0 (saturated)
    runoff: float = 0.0         # mm per day of surface water runoff

    # Soil & Geology
    soil_depth: float = 1.0     # meters of active topsoil layer
    soil_fertility: float = 0.7 # 0.0 (barren) to 1.0 (rich humus)
    erosion: float = 0.0        # mm of topsoil eroded this tick

    # Biology / Vegetation
    vegetation_cover: float = 0.7  # 0.0 (bare earth) to 1.0 (dense canopy)

    def clamp_invariants(self) -> None:
        """
        Enforce physical bounds and conservation rules (Section 13 of blueprint).
        Prevents impossible physical states like negative moisture or cover > 1.0.
        """
        self.soil_moisture = max(0.0, min(1.0, self.soil_moisture))
        self.soil_fertility = max(0.0, min(1.0, self.soil_fertility))
        self.vegetation_cover = max(0.0, min(1.0, self.vegetation_cover))
        self.soil_depth = max(0.01, min(5.0, self.soil_depth))
        self.rainfall = max(0.0, self.rainfall)
        self.runoff = max(0.0, self.runoff)
        self.erosion = max(0.0, self.erosion)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "elevation": round(self.elevation, 1),
            "temperature": round(self.temperature, 2),
            "rainfall": round(self.rainfall, 2),
            "soil_moisture": round(self.soil_moisture, 3),
            "soil_fertility": round(self.soil_fertility, 3),
            "soil_depth": round(self.soil_depth, 3),
            "runoff": round(self.runoff, 2),
            "erosion": round(self.erosion, 4),
            "vegetation_cover": round(self.vegetation_cover, 3),
        }
