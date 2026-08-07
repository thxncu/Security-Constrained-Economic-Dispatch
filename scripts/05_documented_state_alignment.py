"""05 - Documented operating-state alignment and Uri window decomposition.

Regenerates:
  results/table8_documented_state_alignment.csv (main Table 8)
  results/uri_window_decomposition.csv           (Section 5.3: shares inside EEA/shed windows)
  figures/figure3_uri_trajectory.png             (main Figure 3)

Uri documented windows (Section 5.3): EEA1 at 00:15 on 2021-02-15 from the FERC/NERC
event report; EEA3 at 01:20, firm shed to 23:55 on 2021-02-17 and EEA to 09:00 on
2021-02-19 from the Argonne ANL-21/29 timeline.
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
    """Matches the figure embedded in the article (v4): green PRC trace, red
    shaded EEA / firm-shed windows, dotted EEA1-3 trigger lines with labels."""
    import matplotlib.dates as mdates
    iv = io.load_interval_reserve("uri_2021")
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    ax.axvspan(pd.Timestamp(URI_EEA_WINDOW[0]), pd.Timestamp(URI_EEA_WINDOW[1]),
               color="#f5c6c6", alpha=0.45, zorder=0,
               label="EEA window (Feb 15 00:15-Feb 19 09:00)")
    ax.axvspan(pd.Timestamp(URI_SHED_WINDOW[0]), pd.Timestamp(URI_SHED_WINDOW[1]),
               color="#e8a0a0", alpha=0.65, zorder=0,
               label="Firm load shed (to Feb 17 23:55)")
    ax.plot(iv["slot"], iv["prc_mw"] / 1000.0, lw=0.9, color="#2ca02c",
            label="PRC", zorder=2)
    for lvl_gw, name in ((2.3, "EEA1 2,300"), (1.75, "EEA2 1,750"), (1.375, "EEA3 1,375")):
        ax.axhline(lvl_gw, ls=":", color="0.45", lw=0.9, zorder=1)
        ax.annotate(name, xy=(0.045, lvl_gw), xycoords=("axes fraction", "data"),
                    va="bottom", fontsize=7, color="0.4")
    ax.set_title("Winter Storm Uri: SCED PRC vs documented emergency-state windows",
                 fontsize=10)
    ax.set_ylabel("PRC (GW)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.grid(True, alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index("PRC"),
             labels.index("EEA window (Feb 15 00:15-Feb 19 09:00)"),
             labels.index("Firm load shed (to Feb 17 23:55)")]
    ax.legend([handles[k] for k in order], [labels[k] for k in order],
              fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "figure3_uri_trajectory.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    documented_state_table().to_csv(RES / "table8_documented_state_alignment.csv", index=False)
    uri_decomposition().to_csv(RES / "uri_window_decomposition.csv", index=False)
    figure3()
    print("05: wrote table8_documented_state_alignment.csv, uri_window_decomposition.csv, figure3_uri_trajectory.png")
