"""11 - Supplementary figures S1-S5.

Regenerates:
  figures/figureS1_load_prc.png        (S1: load and minimum PRC trajectories)
  figures/figureS2_residual_rtordpa.png (S2: hourly REE residual vs RTORDPA)
  figures/figureS3_three_event_chi.png  (S3: three-event chi comparison, 15 GW)
  figures/figureS4_prc_wind_profiles.png (S4: minimum PRC and wind-derating profiles)
  figures/figureS5_peak_fuel.png        (S5: fuel-category output at peak-load hour)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, shocks, config as C

FIG = C.FIGURES_DIR
FIG.mkdir(exist_ok=True)


def figS1_load_prc():
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.6))
    for ax, ev in zip(axes, C.EVENT_ORDER):
        h = io.load_hourly_panel(ev)
        ax.plot(h["hour"], h["load_mw"] / 1000, label="Load")
        ax.plot(h["hour"], h["prc_min_mw"] / 1000, label="Minimum PRC")
        ax.set_ylabel("GW")
        ax.set_title(C.EVENTS[ev]["label"])
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "figureS1_load_prc.png", dpi=200)
    plt.close(fig)


def figS2_residual_rtordpa():
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.6), sharey=True)
    for ax, ev in zip(axes, C.EVENT_ORDER):
        iv = io.load_interval_reserve(ev).copy()
        iv["hour"] = iv["slot"].dt.floor("h")
        buf = np.maximum(iv["prc_mw"].to_numpy() - 3000.0, 0.0)
        iv["residual_gw"] = np.maximum(15000 - buf, 0.0) / 1000.0
        hourly = iv.groupby("hour").agg(residual_gw=("residual_gw", "mean"),
                                        rtordpa=("rtordpa", "max")).reset_index()
        ax.plot(hourly["hour"], hourly["residual_gw"], color="tab:blue", label="15 GW REE residual (GW)")
        ax2 = ax.twinx()
        ax2.plot(hourly["hour"], hourly["rtordpa"], color="tab:red", lw=0.8, label="Max RTORDPA")
        ax2.set_yscale("symlog")
        ax.set_title(C.EVENTS[ev]["short"])
        ax.grid(True, alpha=0.3)
        if ax is axes[0]:
            ax.set_ylabel("REE residual (GW)")
        if ax is axes[-1]:
            ax2.set_ylabel("Max RTORDPA (USD/MWh, symlog)")
    fig.tight_layout()
    fig.savefig(FIG / "figureS2_residual_rtordpa.png", dpi=200)
    plt.close(fig)


def figS3_three_event_chi():
    order = C.EVENT_ORDER
    chi = [estimator.ree_native(io.load_interval_reserve(ev), 15000, 3000)["chi"] for ev in order]
    labels = [C.EVENTS[ev]["short"] for ev in order]
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    ax.bar(labels, chi, color=["tab:blue", "tab:orange", "tab:green"])
    for i, c in enumerate(chi):
        ax.text(i, c + 0.01, f"{c:.3f}", ha="center", fontsize=9)
    ax.set_ylabel(r"$\chi$ for 15 GW shock, 3 GW retained")
    ax.set_ylim(0, 1)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "figureS3_three_event_chi.png", dpi=200)
    plt.close(fig)


def figS4_prc_wind_profiles():
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.6))
    for ax, ev in zip(axes, C.EVENT_ORDER):
        iv = io.load_interval_reserve(ev)
        traj = shocks.wind_derating_trajectory(ev, 1.0, iv)  # 100% wind-loss shock = wind output
        ax.plot(iv["slot"], iv["prc_mw"] / 1000, label="Minimum PRC (interval)")
        ax.plot(iv["slot"], traj / 1000, label="100% wind-loss shock", lw=0.8)
        ax.set_ylabel("GW")
        ax.set_title(C.EVENTS[ev]["label"])
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "figureS4_prc_wind_profiles.png", dpi=200)
    plt.close(fig)


def figS5_peak_fuel():
    cats = ["wind_mw", "solar_mw", "gas_mw", "coal_mw", "nuclear_mw"]
    catlabels = ["Wind", "Solar", "Gas", "Coal", "Nuclear"]
    order = C.EVENT_ORDER
    data = {c: [] for c in cats}
    for ev in order:
        h = io.load_hourly_panel(ev)
        fuel = io.load_fuel_panel(ev)
        pk_hour = h.loc[h["load_mw"].idxmax(), "hour"]
        frow = fuel[fuel["datetime"] == pk_hour]
        if frow.empty:
            frow = fuel.iloc[[(fuel["datetime"] - pk_hour).abs().argmin()]]
        f = frow.iloc[0]
        for c in cats:
            data[c].append(float(f[c]) / 1000.0)
    labels = [C.EVENTS[ev]["short"] for ev in order]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    bottom = np.zeros(len(labels))
    for c, cl in zip(cats, catlabels):
        ax.bar(x, data[c], bottom=bottom, label=cl)
        bottom += np.array(data[c])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Peak-hour output (GW)")
    ax.legend(fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "figureS5_peak_fuel.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    figS1_load_prc()
    figS2_residual_rtordpa()
    figS3_three_event_chi()
    figS4_prc_wind_profiles()
    figS5_peak_fuel()
    print("11: wrote figureS1_load_prc.png, figureS2_residual_rtordpa.png, "
          "figureS3_three_event_chi.png, figureS4_prc_wind_profiles.png, figureS5_peak_fuel.png")
