"""
Weather System for World Engine v0.1
Responsible for:
- Atmospheric temperature (seasonal variation + elevation lapse rate)
- Daily precipitation / rainfall patterns
"""

import math
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from artificial_civilization.world.world import World


class WeatherSystem:
    def __init__(self, base_annual_temp: float = 22.0, temp_amplitude: float = 8.0):
        self.base_annual_temp = base_annual_temp
        self.temp_amplitude = temp_amplitude
        # Atmospheric lapse rate: ~6.5°C drop per 1,000 meters elevation
        self.lapse_rate_per_meter = 0.0065

    def update(self, world: "World") -> None:
        """
        Advance atmospheric weather by 1 day.
        Calculates cell-specific temperature and precipitation.
        """
        day = world.day
        # Annual seasonal cycle (365 days)
        season_phase = math.sin(2.0 * math.pi * (day - 80) / 365.0)
        daily_base_temp = self.base_annual_temp + self.temp_amplitude * season_phase

        # Regional atmospheric moisture cycle (periods of wet & dry weather fronts)
        synoptic_wave = math.sin(2.0 * math.pi * day / 28.0)  # ~monthly weather cycle
        rain_probability = 0.35 + 0.20 * synoptic_wave

        for row in world.grid:
            for cell in row:
                # 1. Temperature: depends on season, elevation lapse rate, and daily fluctuation
                elevation_cooling = cell.elevation * self.lapse_rate_per_meter
                daily_jitter = world.rng.uniform(-2.0, 2.0)
                cell.temperature = daily_base_temp - elevation_cooling + daily_jitter

                # 2. Rainfall: orographic lift increases rainfall on higher ground
                orographic_factor = 1.0 + (cell.elevation / 800.0)
                cell_rain_chance = rain_probability * min(1.3, orographic_factor)

                if world.rng.random() < cell_rain_chance:
                    # Exponential intensity: mostly moderate showers, occasionally heavy downpours
                    intensity = world.rng.expovariate(1.0 / 12.0) * orographic_factor
                    cell.rainfall = max(0.0, intensity)
                else:
                    cell.rainfall = 0.0

                cell.clamp_invariants()
