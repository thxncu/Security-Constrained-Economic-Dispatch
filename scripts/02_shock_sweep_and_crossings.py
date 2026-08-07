"""02 - Shock-magnitude sweep, crossing thresholds, and Figure 2.

Regenerates:
  results/table6_chi_crossings.csv   (main Table 6: smallest shock reaching each chi)
  results/sweep_chi_by_shock.csv     (full 1-25 GW sweep, both retained cases)
  figures/figure2_shock_sweep.png    (main Figure 2)
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


def sweep_frame():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for r in C.CENTRAL_RETAINED_GW:
            for g in C.SWEEP_SHOCKS_GW:
                chi = estimator.ree_native(iv, g * 1000.0, r * 1000.0)["chi"]
                rows.append({"event": C.EVENTS[ev]["short"], "retained_gw": r,
                             "shock_gw": g, "chi": chi})
    return pd.DataFrame(rows)


def crossings():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for r in C.CENTRAL_RETAINED_GW:
            row = {"event": C.EVENTS[ev]["label"], "retained_gw": r}
            for t in C.CHI_THRESHOLDS:
                row[f"chi>={t}"] = estimator.first_crossing_gw(iv, r * 1000.0, t)
            rows.append(row)
    return pd.DataFrame(rows)


def figure2(sweep):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), sharey=True)
    for ax, r in zip(axes, C.CENTRAL_RETAINED_GW):
        for ev in C.EVENT_ORDER:
            d = sweep[(sweep["event"] == C.EVENTS[ev]["short"]) & (sweep["retained_gw"] == r)]
            ax.plot(d["shock_gw"], d["chi"], marker="", label=C.EVENTS[ev]["label"])
        ax.axhline(0.10, ls=":", color="0.5", lw=0.8)
        ax.axhline(0.50, ls=":", color="0.5", lw=0.8)
        ax.set_title(f"Retained reserve {r} GW")
        ax.set_xlabel("Shock magnitude (GW)")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel(r"Conditional attenuation factor $\chi$")
    axes[0].legend(fontsize=7, loc="upper left")
    axes[0].set_ylim(0, 1)
    # 2nd-revision addition (R2): make the reading direction self-explanatory.
    axes[1].annotate(r"larger $\chi$ = larger unabsorbed share" "\n(reduced reserve absorption)",
                     xy=(0.97, 0.06), xycoords="axes fraction",
                     ha="right", va="bottom", fontsize=7, color="0.35")
    fig.tight_layout()
    fig.savefig(FIG / "figure2_shock_sweep.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    s = sweep_frame()
    s.to_csv(RES / "sweep_chi_by_shock.csv", index=False)
    crossings().to_csv(RES / "table6_chi_crossings.csv", index=False)
    figure2(s)
    print("02: wrote table6_chi_crossings.csv, sweep_chi_by_shock.csv, figure2_shock_sweep.png")
