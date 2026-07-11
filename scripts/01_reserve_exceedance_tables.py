"""01 - SCED-native reserve-exceedance tables.

Regenerates:
  results/table4_ree_by_event.csv         (main Table 4: REE and chi by event/shock/retained)
  results/table5_retained_anchor_sweep.csv (main Table 5: 15 GW chi across retained anchors)
  results/tableS_overstatement.csv         (hourly-minimum overstatement %, Section 5.1)
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def table4():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for q in C.FIXED_SHOCKS_GW:
            for r in C.CENTRAL_RETAINED_GW:
                out = estimator.ree_native(iv, q * 1000.0, r * 1000.0)
                rows.append({
                    "event": C.EVENTS[ev]["label"], "shock_gw": q, "retained_gw": r,
                    "ree_gwh": round(out["ree_mwh"] / 1000.0),
                    "chi": round(out["chi"], 3), "sced_intervals": out["intervals"],
                })
    return pd.DataFrame(rows)


def table5():
    rows = []
    for r_mw, label in C.RETAINED_ANCHORS:
        row = {"retained_gw": r_mw / 1000.0, "operational_anchor": label}
        for ev in C.EVENT_ORDER:
            iv = io.load_interval_reserve(ev)
            row[C.EVENTS[ev]["short"]] = round(estimator.ree_native(iv, 15000, r_mw)["chi"], 3)
        rows.append(row)
    return pd.DataFrame(rows)


def overstatement():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for q in C.FIXED_SHOCKS_GW:
            for r in C.CENTRAL_RETAINED_GW:
                rows.append({
                    "event": C.EVENTS[ev]["label"], "shock_gw": q, "retained_gw": r,
                    "overstatement_pct": round(estimator.overstatement_pct(iv, q * 1000.0, r * 1000.0), 1),
                })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    table4().to_csv(RES / "table4_ree_by_event.csv", index=False)
    table5().to_csv(RES / "table5_retained_anchor_sweep.csv", index=False)
    overstatement().to_csv(RES / "tableS_overstatement.csv", index=False)
    print("01: wrote table4_ree_by_event.csv, table5_retained_anchor_sweep.csv, tableS_overstatement.csv")
