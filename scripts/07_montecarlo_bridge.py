"""07 - Illustrative Monte Carlo bridge from REE to EUE (Section 6.1, Eq. 3).

Regenerates:
  results/mc_bridge_summary.csv          (EUE, SE, percentiles, per-class contributions)
  results/tableS15_mc_prob_sensitivity.csv (2nd-revision addition: class-conditional
                                          mean REE and EUE reweighted under
                                          alternative class-probability vectors)
  figures/figureS6_mc_bridge.png         (Supplementary Figure S6)

All winter-event-class probabilities are illustrative demonstration values.
Because the bridge EUE is a finite mixture, EUE = sum_c p_c * E[REE | c]; the
sensitivity table exposes the conditional means so any reader can substitute
their own probability vector without re-running the simulation.
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
            axes[0].hist(vals, bins=40, alpha=0.55,
                         label=f"{C.EVENTS[name]['label']} (n={len(vals)})")
    axes[0].set_xlabel("Conditional REE per event (GWh)")
    axes[0].set_ylabel("Draws")
    axes[0].legend(fontsize=7)
    axes[0].set_title("Conditional REE by winter-event class", fontsize=10)
    running = np.cumsum(ree) / (np.arange(len(ree)) + 1)
    axes[1].plot(np.arange(len(ree)), running, lw=0.9, color="#2ca02c")
    axes[1].axhline(out["eue_gwh"], ls=":", color="0.4", lw=0.9,
                    label=f"EUE = E[REE] = {out['eue_gwh']:.0f} GWh/winter (illustrative)")
    axes[1].set_xlabel("Monte Carlo draws")
    axes[1].set_ylabel("Running EUE estimate (GWh/winter)")
    axes[1].legend(fontsize=7, loc="lower right")
    axes[1].set_title("Eq. (3) bridge: running EUE estimate", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "figureS6_mc_bridge.png", dpi=200)
    plt.close(fig)

    # ---- 2nd-revision addition: probability-sensitivity via mixture reweighting.
    cond = montecarlo.class_conditional_means()
    base = C.MC_CLASS_PROBS
    variants = {
        "Baseline demonstration (8/15, 4/15, 2/15, 1/15)": base,
        "Event classes half as frequent":
            {"none": 1 - 0.5 * (7 / 15), "january_2025": 2 / 15,
             "elliott_2022": 1 / 15, "uri_2021": 0.5 / 15},
        "Event classes 1.5x as frequent":
            {"none": 1 - 1.5 * (7 / 15), "january_2025": 6 / 15,
             "elliott_2022": 3 / 15, "uri_2021": 1.5 / 15},
        "Equal event-class probabilities (12/15, 1/15 each)":
            {"none": 12 / 15, "january_2025": 1 / 15,
             "elliott_2022": 1 / 15, "uri_2021": 1 / 15},
        "Uri class half as frequent, others at baseline":
            {"none": 8 / 15 + 0.5 / 15, "january_2025": 4 / 15,
             "elliott_2022": 2 / 15, "uri_2021": 0.5 / 15},
    }
    rows = []
    for name, p in variants.items():
        rows.append({"probability_vector": name,
                     "p_none": round(p["none"], 4),
                     "p_january": round(p["january_2025"], 4),
                     "p_elliott": round(p["elliott_2022"], 4),
                     "p_uri": round(p["uri_2021"], 4),
                     "eue_gwh_per_winter": round(montecarlo.reweight_eue(cond, p))})
    sens = pd.DataFrame(rows)
    # append the conditional means so the table is self-contained
    means = pd.DataFrame([{
        "probability_vector": f"Conditional mean REE given {C.EVENTS[ev]['short']} class (GWh)",
        "eue_gwh_per_winter": round(cond[ev]["mean_gwh"]),
    } for ev in ["january_2025", "elliott_2022", "uri_2021"]])
    pd.concat([sens, means], ignore_index=True).to_csv(
        RES / "tableS15_mc_prob_sensitivity.csv", index=False)

    base_reweighted = montecarlo.reweight_eue(cond, base)
    print(f"07: EUE={out['eue_gwh']:.0f} GWh (SE {out['se_gwh']:.0f}); "
          f"reweighted baseline check {base_reweighted:.0f} GWh; "
          f"wrote mc_bridge_summary.csv, tableS15_mc_prob_sensitivity.csv, figureS6_mc_bridge.png")


if __name__ == "__main__":
    main()
