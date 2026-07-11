"""07 - Illustrative Monte Carlo bridge from REE to EUE (Section 6.1, Eq. 3).

Regenerates:
  results/mc_bridge_summary.csv   (EUE, SE, percentiles, per-class contributions)
  figures/figureS6_mc_bridge.png  (Supplementary Figure S6)

All winter-event-class probabilities are illustrative demonstration values.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import montecarlo, config as C

RES, FIG = C.RESULTS_DIR, C.FIGURES_DIR
RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)


def main():
    out = montecarlo.run_bridge()
    summary = pd.DataFrame([{
        "eue_gwh_per_winter": round(out["eue_gwh"]),
        "mc_standard_error_gwh": round(out["se_gwh"]),
        "p50_gwh": round(out["p50_gwh"]),
        "p95_gwh": round(out["p95_gwh"]),
        "p99_gwh": round(out["p99_gwh"]),
        "draws": out["draws"],
        "contrib_january_gwh": round(out["class_contrib_gwh"].get("january_2025", 0)),
        "contrib_elliott_gwh": round(out["class_contrib_gwh"].get("elliott_2022", 0)),
        "contrib_uri_gwh": round(out["class_contrib_gwh"].get("uri_2021", 0)),
    }])
    summary.to_csv(RES / "mc_bridge_summary.csv", index=False)

    # figure: left = per-class REE distribution (event classes only), right = running EUE
    ree = out["ree_draw"]; cls = out["class_draw"]; classes = out["classes"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    for k, name in enumerate(classes):
        if name == "none":
            continue
        vals = ree[(cls == k) & (ree > 0)]
        if len(vals):
            axes[0].hist(vals, bins=40, histtype="step", label=C.EVENTS[name]["short"])
    axes[0].set_xlabel("Conditional REE (GWh)")
    axes[0].set_ylabel("Draws")
    axes[0].legend(fontsize=7)
    axes[0].set_title("REE by winter-event class")
    running = np.cumsum(ree) / (np.arange(len(ree)) + 1)
    axes[1].plot(np.arange(len(ree)), running, lw=0.9)
    axes[1].axhline(out["eue_gwh"], ls="--", color="0.4", lw=0.9,
                    label=f"EUE = {out['eue_gwh']:.0f} GWh")
    axes[1].set_xlabel("Draw")
    axes[1].set_ylabel("Running EUE (GWh)")
    axes[1].legend(fontsize=7)
    axes[1].set_title("Running EUE estimate")
    fig.tight_layout()
    fig.savefig(FIG / "figureS6_mc_bridge.png", dpi=200)
    plt.close(fig)
    print(f"07: EUE={out['eue_gwh']:.0f} GWh (SE {out['se_gwh']:.0f}); wrote mc_bridge_summary.csv, figureS6_mc_bridge.png")


if __name__ == "__main__":
    main()
