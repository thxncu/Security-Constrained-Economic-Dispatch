"""12 - Figure 1: screening workflow schematic.

Regenerates:
  figures/figure1_workflow.png (main Figure 1: decision flow from event-window
                                definition to the escalation decision)

This figure is a schematic of the workflow described in Section 3.3; it renders the
same box-and-arrow decision flow used in the manuscript.
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import config as C

FIG = C.FIGURES_DIR
FIG.mkdir(exist_ok=True)


def box(ax, xy, w, h, text, fc="#eef3fb", ec="#2b5aa0"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, wrap=True)


def arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12,
                                 lw=1.1, color="#444444"))


def figure1():
    fig, ax = plt.subplots(figsize=(7.2, 8.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    cx, w, h = 2.5, 5.0, 1.05
    ys = [10.4, 8.9, 7.4, 5.9, 4.4]
    steps = [
        "Define event window\n(event report or transparent algorithmic rule)",
        "Build native-interval reserve trajectory\nand hourly load/outage/fuel panels",
        "Specify shock trajectories\n(fixed / event-specific envelope / time-varying wind)",
        "Compute SCED-native REE, attenuation factor chi,\nand hourly-minimum reproduction value",
        "Repeat across retained-reserve levels\nand buffer definitions",
    ]
    for y, s in zip(ys, steps):
        box(ax, (cx, y), w, h, s)
    for i in range(len(ys) - 1):
        arrow(ax, (cx + w / 2, ys[i]), (cx + w / 2, ys[i + 1] + h))

    # consistency check box
    ycheck = 2.9
    box(ax, (cx, ycheck), w, h, "Check consistency against documented\noperating states and scarcity-price adders",
        fc="#fdf2e6", ec="#b5651d")
    arrow(ax, (cx + w / 2, ys[-1]), (cx + w / 2, ycheck + h))

    # decision diamond (as a box for simplicity)
    ydec = 1.2
    box(ax, (cx, ydec), w, h, "Exposure material or sensitive\nto assumptions?", fc="#f6eefb", ec="#7a3fa0")
    arrow(ax, (cx + w / 2, ycheck), (cx + w / 2, ydec + h))

    # outcomes
    box(ax, (0.2, -0.4), 2.9, 1.05, "No: document\nabsorbed shock", fc="#eaf6ea", ec="#2e7d32")
    box(ax, (6.9, -0.4), 2.9, 1.05, "Yes: escalate via Eq. (3)\nto adequacy modelling", fc="#fdeaea", ec="#c62828")
    arrow(ax, (cx + 1.2, ydec), (1.65, 0.65))
    arrow(ax, (cx + w - 1.2, ydec), (8.35, 0.65))

    fig.tight_layout()
    fig.savefig(FIG / "figure1_workflow.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    figure1()
    print("12: wrote figure1_workflow.png")
