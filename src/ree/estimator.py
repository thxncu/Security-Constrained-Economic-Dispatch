"""Reserve-exceedance energy (REE) estimator.

Implements the equations of Section 3:

    Eq. (1)  native conditional REE:  sum_i max(q - B_i, 0) * dt
    Eq. (2)  conditional attenuation factor chi = REE / total stress exposure
    Eq. (4)  retained-reserve buffer:  B = max(PRC - R_ret, 0)
    Eq. (5)  hourly-minimum screen:    max(q - min_i B_i, 0) per hour
    Eq. (6)  native interval integration (same as Eq. 1)

All energies are returned in MWh unless a helper name says otherwise.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from . import config as C


# ----------------------------------------------------------------------------
# Buffer construction (Eq. 4 and buffer-definition variants, Section 3.2 / 5.3).
# ----------------------------------------------------------------------------
def buffer_series(interval: pd.DataFrame, retained_mw: float, buffer: str = "PRC") -> np.ndarray:
    """Return the usable operating buffer (MW) per interval.

    buffer: "PRC" (central), "RTOLCAP", or "RTOLCAP+RTOFFCAP" (Section 5.3).
    """
    if buffer == "PRC":
        base = interval["prc_mw"].to_numpy(dtype=float)
    elif buffer == "RTOLCAP":
        base = interval["rtolcap_mw"].to_numpy(dtype=float)
    elif buffer == "RTOLCAP+RTOFFCAP":
        base = (interval["rtolcap_mw"] + interval["rtoffcap_mw"]).to_numpy(dtype=float)
    else:
        raise ValueError(f"unknown buffer definition: {buffer}")
    return np.maximum(base - retained_mw, 0.0)


# ----------------------------------------------------------------------------
# Native REE and chi (Eqs. 1, 2, 6).
# ----------------------------------------------------------------------------
def ree_native(interval: pd.DataFrame, shock_mw, retained_mw: float,
               buffer: str = "PRC", dt_hours: float = C.INTERVAL_HOURS) -> dict:
    """Native-integrated REE and chi for a scalar or per-interval shock.

    shock_mw: scalar (fixed shock) or array aligned to the interval rows
              (time-varying shock, Section 3.3 / 5.2).
    Returns a dict with ree_mwh, chi, intervals, hours_at_risk_equiv.
    """
    B = buffer_series(interval, retained_mw, buffer)
    q = np.asarray(shock_mw, dtype=float)
    if q.ndim == 0:
        q = np.full(B.shape, float(q))
    exceed = np.maximum(q - B, 0.0)
    ree_mwh = float(exceed.sum() * dt_hours)
    exposure_mwh = float(q.sum() * dt_hours)
    chi = ree_mwh / exposure_mwh if exposure_mwh > 0 else 0.0
    at_risk = int((exceed > 0).sum())
    return {
        "ree_mwh": ree_mwh,
        "chi": chi,
        "intervals": int(len(B)),
        "hours_at_risk_equiv": at_risk * dt_hours,
    }


# ----------------------------------------------------------------------------
# Hourly-minimum screen (Eq. 5, Section 3.3) and the overstatement it produces.
# ----------------------------------------------------------------------------
def ree_hourly_minimum(interval: pd.DataFrame, shock_mw: float, retained_mw: float,
                       buffer: str = "PRC") -> dict:
    """Hourly-minimum reproduction screen for a constant hourly shock.

    Aggregates the buffer to an hourly minimum, applies the shock to that minimum
    for the whole hour, and integrates. Returns ree_mwh and chi.
    """
    B = buffer_series(interval, retained_mw, buffer)
    hours = interval["slot"].dt.floor("h").to_numpy()
    df = pd.DataFrame({"hour": hours, "B": B})
    hmin = df.groupby("hour")["B"].min()
    hours_count = df.groupby("hour").size()
    exceed_per_hour = np.maximum(float(shock_mw) - hmin.to_numpy(), 0.0)
    # each hour contributes (n intervals in hour) * dt hours of that constant value
    ree_mwh = float((exceed_per_hour * hours_count.to_numpy() * C.INTERVAL_HOURS).sum())
    exposure_mwh = float(shock_mw * len(B) * C.INTERVAL_HOURS)
    chi = ree_mwh / exposure_mwh if exposure_mwh > 0 else 0.0
    return {"ree_mwh": ree_mwh, "chi": chi}


def overstatement_pct(interval: pd.DataFrame, shock_mw: float, retained_mw: float,
                      buffer: str = "PRC") -> float:
    """Percentage by which the hourly-minimum screen overstates native REE."""
    native = ree_native(interval, shock_mw, retained_mw, buffer)["ree_mwh"]
    hmin = ree_hourly_minimum(interval, shock_mw, retained_mw, buffer)["ree_mwh"]
    if native <= 0:
        return float("nan")
    return 100.0 * (hmin - native) / native


# ----------------------------------------------------------------------------
# chi-crossing search (Section 5.2, Table 6).
# ----------------------------------------------------------------------------
def first_crossing_gw(interval: pd.DataFrame, retained_mw: float, chi_target: float,
                      shocks_gw=None, buffer: str = "PRC") -> float:
    """Smallest integer-GW shock at which chi first reaches chi_target."""
    shocks_gw = shocks_gw or C.SWEEP_SHOCKS_GW
    for g in shocks_gw:
        chi = ree_native(interval, g * 1000.0, retained_mw, buffer)["chi"]
        if chi >= chi_target:
            return float(g)
    return float("nan")


# ----------------------------------------------------------------------------
# Incidence / depth decomposition (Section 5.3, Table S8-equivalent mechanism).
# ----------------------------------------------------------------------------
def incidence_depth(interval: pd.DataFrame, shock_mw: float, retained_mw: float,
                    buffer: str = "PRC") -> dict:
    """Decompose exceedance into incidence (share of intervals in exceedance) and
    mean exceedance depth (GW) over intervals that are in exceedance."""
    B = buffer_series(interval, retained_mw, buffer)
    exceed = np.maximum(float(shock_mw) - B, 0.0)
    in_exc = exceed > 0
    incidence = float(in_exc.mean())
    mean_depth_gw = float(exceed[in_exc].mean() / 1000.0) if in_exc.any() else 0.0
    return {"incidence": incidence, "mean_depth_gw": mean_depth_gw}
