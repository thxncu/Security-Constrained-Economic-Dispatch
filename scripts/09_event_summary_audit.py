"""09 - Three-event operating-data summary and interval audit.

Regenerates:
  results/table3_event_summary.csv  (main Table 3: operating-data summary)
  results/tableS3_interval_audit.csv (Supplementary S3: interval completeness)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def summary():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        h = io.load_hourly_panel(ev)
        prc = iv["prc_mw"].to_numpy()
        rtordpa = iv["rtordpa"].to_numpy()
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "hours": C.EVENTS[ev]["hours"],
            "peak_load_mw": round(float(h["load_mw"].max())),
            "min_prc_mw": round(float(prc.min())),
            "hours_prc_below_8gw": int((h["prc_min_mw"] < C.TIGHT_PRC_MW).sum()),
            "rtordpa_gt0_hours": int((h["rtordpa_max"] > 0).sum()),
            "rtordpa_gt10_hours": int((h["rtordpa_max"] > 10).sum()),
            "max_rtordpa": round(float(rtordpa.max()), 2),
            "max_res_irr_outage_mw": round(float(h["res_irr_outage_mw"].max())),
        })
    return pd.DataFrame(rows)


def interval_audit():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        h = io.load_hourly_panel(ev)
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "hours": C.EVENTS[ev]["hours"],
            "expected_sced_intervals": C.EVENTS[ev]["expected_intervals"],
            "sced_intervals": int(len(iv)),
            "load_hours": int(h["load_mw"].notna().sum()),
            "outage_hours": int(h["res_irr_outage_mw"].notna().sum()),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    summary().to_csv(RES / "table3_event_summary.csv", index=False)
    interval_audit().to_csv(RES / "tableS3_interval_audit.csv", index=False)
    print("09: wrote table3_event_summary.csv, tableS3_interval_audit.csv")
