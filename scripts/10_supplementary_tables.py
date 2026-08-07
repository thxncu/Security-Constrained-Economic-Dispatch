"""10 - Remaining supplementary tables.

Regenerates:
  results/tableS2_data_layers.csv          (Supplementary S2: public-data layers)
  results/tableS5_report_anchors.csv       (Supplementary S5: report-level severity anchors)
  results/tableS11_jan_snapshot_sensitivity.csv (Supplementary S11: outage-snapshot rule sensitivity)
  results/tableS12_jan_dedup_sensitivity.csv     (Supplementary S12: SCED duplicate-run sensitivity)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def data_layers():
    return pd.DataFrame(C.DATA_LAYERS, columns=["layer", "public_data_product", "use_in_analysis", "events"])


def report_anchors():
    rows = []
    for ev in C.EVENT_ORDER:
        h = io.load_hourly_panel(ev)
        max_res_irr = float(h["res_irr_outage_mw"].max())
        max_env = float(h["all_outage_mw"].max())
        unavail, shed, interp = C.REPORT_ANCHORS[ev]
        ratio = shed / unavail if unavail else 0.0
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "max_res_irr_outage_mw": round(max_res_irr),
            "max_all_envelope_mw": round(max_env),
            "reported_unavailable_generation_mw": unavail,
            "firm_load_shed_mw": shed,
            "report_ratio": round(ratio, 3),
            "interpretation": interp,
        })
    return pd.DataFrame(rows)


def jan_snapshot_sensitivity():
    v = pd.read_csv(C.SENSITIVITY_DIR / "january_2025_outage_snapshot_variants.csv",
                    parse_dates=["hour_start"])
    rule_label = {"contemporaneous": "Contemporaneous central", "latest_overall": "Latest overall"}
    rows = []
    for wlabel, (lo, hi) in C.JAN_SNAPSHOT_WINDOWS.items():
        for rule in ["contemporaneous", "latest_overall"]:
            sub = v[(v["rule"] == rule) & (v["hour_start"] >= lo) & (v["hour_start"] < hi)]
            rows.append({
                "window": wlabel,
                "snapshot_rule": rule_label[rule],
                "max_res_irr_mw": round(float(sub["res_irr_mw"].max())),
                "max_all_envelope_mw": round(float(sub["all_env_mw"].max())),
                "mean_res_irr_mw": round(float(sub["res_irr_mw"].mean())),
            })
    return pd.DataFrame(rows)


def jan_dedup_sensitivity():
    d = pd.read_csv(C.SENSITIVITY_DIR / "january_2025_dedup_variants.csv")
    rule_col = {"Latest SCED run": "prc_latest", "First SCED run": "prc_first", "Mean within slot": "prc_mean"}
    rows = []
    for rule, col in rule_col.items():
        prc = d[col].to_numpy()
        for r in [0, 3000]:
            buf = np.maximum(prc - r, 0.0)
            ree_mwh = float(np.maximum(15000 - buf, 0.0).sum() * C.INTERVAL_HOURS)
            chi = ree_mwh / (15000 * len(prc) * C.INTERVAL_HOURS)
            rows.append({
                "deduplication_rule": rule,
                "retained_gw": r / 1000.0,
                "ree_mwh": round(ree_mwh),
                "chi": round(chi, 3),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data_layers().to_csv(RES / "tableS2_data_layers.csv", index=False)
    report_anchors().to_csv(RES / "tableS5_report_anchors.csv", index=False)
    jan_snapshot_sensitivity().to_csv(RES / "tableS11_jan_snapshot_sensitivity.csv", index=False)
    jan_dedup_sensitivity().to_csv(RES / "tableS12_jan_dedup_sensitivity.csv", index=False)
    print("10: wrote tableS2_data_layers.csv, tableS5_report_anchors.csv, "
          "tableS11_jan_snapshot_sensitivity.csv, tableS12_jan_dedup_sensitivity.csv")
