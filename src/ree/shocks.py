"""Shock-trajectory families (Section 3.3).

Three families are supported:

  1. Fixed common shock:            a scalar q applied to every interval.
  2. Event-specific envelope shock: a scalar tied to the event's own maximum
                                     resource-plus-IRR outage envelope.
  3. Time-varying wind-derating:    q(tau) = alpha * W(tau), with concurrent hourly
                                     wind output held constant across the native
                                     intervals inside the hour.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from . import io, config as C


def fixed_shock(interval: pd.DataFrame, shock_gw: float) -> float:
    """Family 1: a scalar shock (GW -> MW)."""
    return float(shock_gw) * 1000.0


def envelope_shock_mw(event: str, fraction: float = 1.0) -> float:
    """Family 2: fraction of the event's maximum resource+IRR outage envelope (MW).

    The envelope is taken from the hourly panel's res_irr_outage_mw column.
    """
    h = io.load_hourly_panel(event)
    return float(fraction * h["res_irr_outage_mw"].max())


def wind_derating_trajectory(event: str, alpha: float, interval: pd.DataFrame) -> np.ndarray:
    """Family 3: per-interval shock q(tau) = alpha * W(tau) (MW).

    Hourly wind output is broadcast to the five-minute intervals within each hour,
    matching the manuscript's hourly derating resolution (Section 3.3).
    """
    fuel = io.load_fuel_panel(event)[["datetime", "wind_mw"]].copy()
    fuel["hour"] = fuel["datetime"].dt.floor("h")
    wind_by_hour = fuel.set_index("hour")["wind_mw"]
    hours = interval["slot"].dt.floor("h")
    w = hours.map(wind_by_hour).to_numpy(dtype=float)
    # any interval hour without a wind value (edge alignment) contributes zero shock
    w = np.nan_to_num(w, nan=0.0)
    return alpha * w


def equal_energy_constant_gw(trajectory_mw: np.ndarray) -> float:
    """The constant shock (GW) with the same total energy as a time-varying trajectory,
    used for the equal-energy comparison (Section 5.2, Table 7)."""
    if len(trajectory_mw) == 0:
        return 0.0
    return float(trajectory_mw.mean() / 1000.0)
