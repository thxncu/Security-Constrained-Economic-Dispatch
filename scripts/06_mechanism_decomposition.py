"""06 - Mechanism: incidence/depth decomposition, tight-hour composition, peak fuel.

Regenerates:
  results/tableS9_peak_fuel.csv           (Supplementary S9: fuel at peak-load hour)
  results/tableS10_tight_hour_context.csv (Supplementary S10: tight vs other-hour composition)
  results/incidence_depth.csv             (Section 5.3: Uri-Elliott gap decomposition)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def peak_fuel():
    rows = []
    for ev in C.EVENT_ORDER:
        h = io.load_hourly_panel(ev)
        fuel = io.load_fuel_panel(ev)
        pk_hour = h.loc[h["load_mw"].idxmax(), "hour"]
        frow = fuel[fuel["datetime"] == pk_hour]
        if frow.empty:
            # nearest hour fallback
            frow = fuel.iloc[(fuel["datetime"] - pk_hour).abs().argmin():].head(1)
        f = frow.iloc[0]
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "peak_load_hour": str(pk_hour),
            "load_mw": round(float(h["load_mw"].max())),
            "wind_mw": round(float(f["wind_mw"])),
            "solar_mw": round(float(f["solar_mw"])),
            "gas_mw": round(float(f["gas_mw"])),
            "coal_mw": round(float(f["coal_mw"])),
            "nuclear_mw": round(float(f["nuclear_mw"])),
        })
    return pd.DataFrame(rows)


def tight_hour_context():
    rows = []
    for ev in C.EVENT_ORDER:
        h = io.load_hourly_panel(ev).copy()
        fuel = io.load_fuel_panel(ev).rename(columns={"datetime": "hour"})
        h = h.merge(fuel[["hour", "wind_mw", "gas_mw"]], on="hour", how="left", suffixes=("", "_fuel"))
        wind_col = "wind_mw_fuel" if "wind_mw_fuel" in h.columns else "wind_mw"
        gas_col = "gas_mw_fuel" if "gas_mw_fuel" in h.columns else "gas_mw"
        event_wind_max = h[wind_col].max()
        h["tight"] = h["prc_min_mw"] < C.TIGHT_PRC_MW
        for is_tight, label in [(True, "Tight"), (False, "Other")]:
            g = h[h["tight"] == is_tight]
            if g.empty:
                continue
            rows.append({
                "event": C.EVENTS[ev]["label"], "hour_class": label,
                "hours": int(len(g)),
                "mean_wind_mw": round(float(g[wind_col].mean())),
                "wind_share_of_event_max_pct": round(100.0 * g[wind_col].mean() / event_wind_max) if event_wind_max else 0,
                "mean_gas_mw": round(float(g[gas_col].mean())),
                "mean_res_irr_outage_mw": round(float(g["res_irr_outage_mw"].mean())),
                "mean_load_mw": round(float(g["load_mw"].mean())),
            })
    return pd.DataFrame(rows)


def incidence_depth_gap():
    rows = []
    for ev in ["uri_2021", "elliott_2022"]:
        iv = io.load_interval_reserve(ev)
        d = estimator.incidence_depth(iv, 15000, 0)
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "incidence": round(d["incidence"], 3),
            "mean_depth_gw": round(d["mean_depth_gw"], 2),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    peak_fuel().to_csv(RES / "tableS9_peak_fuel.csv", index=False)
    tight_hour_context().to_csv(RES / "tableS10_tight_hour_context.csv", index=False)
    incidence_depth_gap().to_csv(RES / "incidence_depth.csv", index=False)
    print("06: wrote tableS9_peak_fuel.csv, tableS10_tight_hour_context.csv, incidence_depth.csv")
