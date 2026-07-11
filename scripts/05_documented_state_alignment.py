"""05 - Documented operating-state alignment and Uri window decomposition.

Regenerates:
  results/table8_documented_state_alignment.csv (main Table 8)
  results/uri_window_decomposition.csv           (Section 5.3: shares inside EEA/shed windows)
  figures/figure3_uri_trajectory.png             (main Figure 3)

The Uri documented windows follow the Argonne ANL-21/29 timeline (Section 5.3):
  EEA1 at 00:15 on 2021-02-15, firm shed to 23:55 on 2021-02-17, EEA to 09:00 on 2021-02-19.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, config as C

RES, FIG = C.RESULTS_DIR, C.FIGURES_DIR
RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

URI_EEA_WINDOW = ("2021-02-15 00:15", "2021-02-19 09:00")
URI_SHED_WINDOW = ("2021-02-15 01:20", "2021-02-17 23:55")


def documented_state_table():
    rows = []
    meta = {
        "january_2025": "TXANS Weather Watch Jan. 20-23; no conservation appeal; no EEA",
        "elliott_2022": "No EEA; watch-level communications only",
        "uri_2021": "EEA1 Feb. 15 00:15; EEA3 01:20; firm shed to Feb. 17 23:55; EEA to Feb. 19 09:00",
    }
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        prc = iv["prc_mw"].to_numpy()
        trig = C.EVENTS[ev]["eea1_trigger_mw"]
        hours_below = float((prc < trig).sum() * C.INTERVAL_HOURS)
        r3 = estimator.ree_native(iv, 15000, 3000)["ree_mwh"] / 1000.0
        rows.append({
            "event": C.EVENTS[ev]["label"],
            "documented_operating_state": meta[ev],
            "eea1_trigger_mw": trig,
            "min_prc_mw": round(float(prc.min())),
            "hours_equiv_prc_below_eea1": round(hours_below, 1),
            "ree_15gw_retained3_gwh": round(r3),
        })
    return pd.DataFrame(rows)


def uri_decomposition():
    iv = io.load_interval_reserve("uri_2021")
    slot = iv["slot"]
    prc = iv["prc_mw"].to_numpy()
    in_eea = ((slot >= URI_EEA_WINDOW[0]) & (slot < URI_EEA_WINDOW[1])).to_numpy()
    in_shed = ((slot >= URI_SHED_WINDOW[0]) & (slot < URI_SHED_WINDOW[1])).to_numpy()
    rows = []
    for r in [0, 3000]:
        buf = np.maximum(prc - r, 0.0)
        exceed = np.maximum(15000 - buf, 0.0) * C.INTERVAL_HOURS  # MWh per interval
        total = exceed.sum() / 1000.0
        rows.append({
            "retained_gw": r / 1000.0,
            "ree_total_gwh": round(total),
            "ree_in_shed_gwh": round(exceed[in_shed].sum() / 1000.0),
            "share_in_shed_pct": round(100.0 * exceed[in_shed].sum() / exceed.sum(), 1),
            "ree_in_eea_gwh": round(exceed[in_eea].sum() / 1000.0),
            "share_in_eea_pct": round(100.0 * exceed[in_eea].sum() / exceed.sum(), 1),
        })
    return pd.DataFrame(rows)


def figure3():
    iv = io.load_interval_reserve("uri_2021")
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    ax.plot(iv["slot"], iv["prc_mw"] / 1000.0, lw=0.8, label="PRC")
    ax.axhline(2.3, ls="--", color="0.4", lw=0.9, label="EEA1 trigger (2.3 GW)")
    ax.axvspan(pd.Timestamp(URI_SHED_WINDOW[0]), pd.Timestamp(URI_SHED_WINDOW[1]),
               color="0.85", label="Firm-load-shed window")
    ax.axvspan(pd.Timestamp(URI_EEA_WINDOW[0]), pd.Timestamp(URI_EEA_WINDOW[1]),
               color="0.93", zorder=0, label="EEA window")
    ax.set_ylabel("PRC (GW)")
    ax.set_xlabel("2021")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "figure3_uri_trajectory.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    documented_state_table().to_csv(RES / "table8_documented_state_alignment.csv", index=False)
    uri_decomposition().to_csv(RES / "uri_window_decomposition.csv", index=False)
    figure3()
    print("05: wrote table8_documented_state_alignment.csv, uri_window_decomposition.csv, figure3_uri_trajectory.png")
