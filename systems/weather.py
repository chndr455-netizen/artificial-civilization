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

        # Regional Weather Front Dynamics (Natural episodic weather)
        self.is_storming: bool = False
        self.storm_duration: int = 0
        self.days_since_storm: int = 4
        self.next_storm_in: int = 6

    def update(self, world: "World") -> None:
        """
        Advance atmospheric weather by 1 day.
        Simulates natural episodic weather: multi-day dry spells (4-12 days)
        punctuated by 1-2 day regional weather fronts / storm events.
        """
        day = world.day
        # Annual seasonal cycle (365 days)
        season_phase = math.sin(2.0 * math.pi * (day - 80) / 365.0)
        daily_base_temp = self.base_annual_temp + self.temp_amplitude * season_phase

        # Seasonal wet/dry season modulation (~monthly synoptic cycle)
        synoptic_wave = math.sin(2.0 * math.pi * day / 28.0)
        # Wet seasons have shorter intervals between storms; dry seasons have longer intervals
        target_interval_min = max(3, int(6 - 2 * synoptic_wave))
        target_interval_max = max(target_interval_min + 3, int(12 - 3 * synoptic_wave))

        # Weather Front State Progression
        if self.is_storming:
            self.storm_duration -= 1
            if self.storm_duration <= 0:
                self.is_storming = False
                self.days_since_storm = 0
                self.next_storm_in = world.rng.randint(target_interval_min, target_interval_max)
        else:
            self.days_since_storm += 1
            if self.days_since_storm >= self.next_storm_in:
                self.is_storming = True
                # Storms last 1-2 days
                self.storm_duration = 1 if world.rng.random() < 0.7 else 2

        # Base regional precipitation intensity for today
        regional_rain_intensity = 0.0
        if self.is_storming:
            # Concentrated storm rainfall: 10 - 35 mm for an episodic rain event
            regional_rain_intensity = world.rng.uniform(12.0, 32.0)

        for row in world.grid:
            for cell in row:
                # 1. Temperature: seasonal wave - elevation lapse rate + gentle micro-jitter
                elevation_cooling = cell.elevation * self.lapse_rate_per_meter
                daily_jitter = world.rng.uniform(-1.2, 1.2)
                cell.temperature = daily_base_temp - elevation_cooling + daily_jitter

                # 2. Precipitation: if storm front active, orographic lift modulates rain
                if self.is_storming:
                    orographic_factor = 1.0 + (cell.elevation / 900.0)
                    cell_jitter = world.rng.uniform(0.85, 1.15)
                    cell.rainfall = max(0.0, regional_rain_intensity * orographic_factor * cell_jitter)
                else:
                    cell.rainfall = 0.0

                cell.clamp_invariants()
