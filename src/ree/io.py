"""Loaders for the derived (copyright-safe) event panels.

None of these functions read raw ERCOT files. They read the derived panels shipped
in ``data/`` that were produced from public ERCOT products by ``scripts/00_derive_panels``
(documented in ``data/PROVENANCE.md``).
"""
from __future__ import annotations
import pandas as pd

from . import config as C


def _slice(df: pd.DataFrame, tcol: str, event: str) -> pd.DataFrame:
    lo, hi = C.EVENTS[event]["window"]
    m = (df[tcol] >= lo) & (df[tcol] < hi)
    return df.loc[m].sort_values(tcol).reset_index(drop=True)


def load_interval_reserve(event: str) -> pd.DataFrame:
    """Native five-minute reserve series for an event.

    Columns: slot (datetime), prc_mw, rtolcap_mw, rtoffcap_mw, rtordpa.
    This is the analytical input to the native REE integration of Eq. (6).
    """
    df = pd.read_csv(C.INTERVAL_DIR / f"{event}_interval_reserve.csv", parse_dates=["slot"])
    return _slice(df, "slot", event)


def load_hourly_panel(event: str) -> pd.DataFrame:
    """Hourly merged panel for an event (load, PRC aggregates, outage, fuel where present).

    The January 2025 panel uses ``hour_start`` and a different column vocabulary; it is
    normalised here to a common minimal schema: hour, load_mw, prc_min_mw, prc_mean_mw,
    rtordpa_max, sced_intervals, res_irr_outage_mw, all_outage_mw.
    """
    if event == "january_2025":
        df = pd.read_csv(C.HOURLY_DIR / f"{event}_hourly_panel.csv", parse_dates=["hour_start"])
        out = pd.DataFrame({
            "hour": df["hour_start"],
            "load_mw": df["load_total_weatherzone"],
            "prc_min_mw": df["prc_min"],
            "prc_mean_mw": df["prc_mean"],
            "rtordpa_max": df["rtordpa_max"],
            "sced_intervals": df["n_sced"],
            "res_irr_outage_mw": df["res_irr_outage_mw"],
            "all_outage_mw": df["all_envelope_mw"],
        })
        return _slice(out, "hour", event)
    df = pd.read_csv(C.HOURLY_DIR / f"{event}_hourly_panel.csv", parse_dates=["datetime"])
    out = df.rename(columns={
        "datetime": "hour",
        "res_irr_outage_mw": "res_irr_outage_mw",
        "all_outage_mw": "all_outage_mw",
    })
    keep = ["hour", "load_mw", "prc_min_mw", "prc_mean_mw", "rtordpa_max",
            "sced_intervals", "res_irr_outage_mw", "all_outage_mw",
            "wind_mw", "solar_mw", "gas_mw", "coal_mw", "nuclear_mw"]
    out = out[[c for c in keep if c in out.columns]]
    return _slice(out, "hour", event)


def load_fuel_panel(event: str) -> pd.DataFrame:
    """Hourly fuel-category output (MW) for an event.

    Columns: datetime, wind_mw, solar_mw, gas_mw, coal_mw, nuclear_mw, fuel_total_mw.
    """
    df = pd.read_csv(C.FUEL_DIR / f"{event}_fuel_panel.csv", parse_dates=["datetime"])
    return _slice(df, "datetime", event)


def load_outage_snapshot(event: str) -> pd.DataFrame:
    """Hourly outage-capacity snapshot (last report at or before each hour end)."""
    df = pd.read_csv(C.OUTAGE_DIR / f"{event}_outage_snapshot.csv")
    return df
