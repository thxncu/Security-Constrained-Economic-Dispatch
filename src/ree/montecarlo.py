"""Illustrative Monte Carlo bridge from conditional REE to EUE (Section 6.1, Eq. 3).

This is a demonstration of the Eq. (3) mechanics, not a calibrated adequacy model.
All winter-event-class probabilities are illustrative demonstration values.

For each draw:
  1. sample a winter-event class from the demonstration probabilities;
  2. if the class is an event, sample a shock from a truncated normal and a
     day-block bootstrap of that event's five-minute buffer, then evaluate native
     REE on the resampled buffer;
  3. the "none" class contributes zero.
The mean over draws is the demonstration EUE per winter.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from . import io, estimator, config as C


def _day_blocks(prc_mw, slots, retained_mw):
    """Return a list of per-day buffer (B = max(PRC - retained, 0)) arrays."""
    B = np.maximum(prc_mw - retained_mw, 0.0)
    days = pd.Series(slots).dt.floor("D")
    return [B[(days == d).to_numpy()] for d in days.unique()]


def run_bridge(seed: int = C.MC_SEED, draws: int = C.MC_DRAWS) -> dict:
    """Run the demonstration bridge and return summary statistics and per-class contributions.

    The random-number draw order (class choice, then per-draw shock and day-block
    bootstrap) matches the manuscript's Monte Carlo so that the reported EUE, standard
    error, and percentiles reproduce exactly.
    """
    rng = np.random.default_rng(seed)
    retained = 3000.0

    ev_blocks = {}
    for ev in ["january_2025", "elliott_2022", "uri_2021"]:
        iv = io.load_interval_reserve(ev)
        ev_blocks[ev] = _day_blocks(iv["prc_mw"].to_numpy(dtype=float), iv["slot"].to_numpy(), retained)

    classes = list(C.MC_CLASS_PROBS.keys())
    probs = np.array([C.MC_CLASS_PROBS[c] for c in classes])
    probs = probs / probs.sum()

    def draw_ree(cls):
        if cls == "none":
            return 0.0
        q = float(np.clip(rng.normal(C.MC_SHOCK["mean"], C.MC_SHOCK["sd"]),
                          C.MC_SHOCK["lo"], C.MC_SHOCK["hi"]))
        blocks = ev_blocks[cls]
        idx = rng.integers(0, len(blocks), size=len(blocks))  # day-block bootstrap
        B = np.concatenate([blocks[i] for i in idx])
        return np.maximum(q - B, 0.0).sum() * C.INTERVAL_HOURS  # MWh

    class_draw = rng.choice(len(classes), size=draws, p=probs)
    ree = np.zeros(draws)
    for i, ci in enumerate(class_draw):
        ree[i] = draw_ree(classes[ci])

    ree_gwh = ree / 1000.0
    eue = float(ree_gwh.mean())
    se = float(ree_gwh.std(ddof=1) / np.sqrt(draws))
    contrib = {cls: float(ree_gwh[class_draw == k].sum() / draws) for k, cls in enumerate(classes)}

    return {
        "eue_gwh": eue,
        "se_gwh": se,
        "p50_gwh": float(np.percentile(ree_gwh, 50)),
        "p95_gwh": float(np.percentile(ree_gwh, 95)),
        "p99_gwh": float(np.percentile(ree_gwh, 99)),
        "draws": draws,
        "class_contrib_gwh": contrib,
        "ree_draw": ree_gwh,
        "class_draw": class_draw,
        "classes": classes,
    }


# ----------------------------------------------------------------------------
# 2nd-revision additions (Reviewer 3, round 2): class-conditional decomposition
# and probability reweighting.
#
# Because the bridge EUE is a finite mixture, EUE(p) = sum_c p_c * m_c where
# m_c = E[REE | class c] and the "none" class contributes zero. The class
# probabilities therefore enter linearly, and any reader can substitute an
# alternative probability vector without re-running the simulation. The
# functions below estimate the conditional means m_c once and reweight them
# under alternative demonstration probability vectors.
# ----------------------------------------------------------------------------
def class_conditional_means(seed: int = C.MC_SEED + 1, draws_per_class: int = 20000,
                            retained_mw: float = 3000.0) -> dict:
    """Estimate m_c = E[REE | class c] in GWh per event class, with MC SEs.

    Uses the same truncated-normal shock and day-block bootstrap as run_bridge,
    but simulates each event class separately so that the conditional means are
    estimated with equal precision. A separate seed keeps run_bridge's published
    draw sequence untouched.
    """
    rng = np.random.default_rng(seed)
    out = {}
    for ev in ["january_2025", "elliott_2022", "uri_2021"]:
        iv = io.load_interval_reserve(ev)
        B_all = np.maximum(iv["prc_mw"].to_numpy(dtype=float) - retained_mw, 0.0)
        days = pd.Series(iv["slot"]).dt.floor("D")
        blocks = [B_all[(days == d).to_numpy()] for d in days.unique()]
        vals = np.empty(draws_per_class)
        for i in range(draws_per_class):
            q = float(np.clip(rng.normal(C.MC_SHOCK["mean"], C.MC_SHOCK["sd"]),
                              C.MC_SHOCK["lo"], C.MC_SHOCK["hi"]))
            idx = rng.integers(0, len(blocks), size=len(blocks))
            B = np.concatenate([blocks[i2] for i2 in idx])
            vals[i] = np.maximum(q - B, 0.0).sum() * C.INTERVAL_HOURS / 1000.0  # GWh
        out[ev] = {"mean_gwh": float(vals.mean()),
                   "se_gwh": float(vals.std(ddof=1) / np.sqrt(draws_per_class)),
                   "draws": draws_per_class}
    out["none"] = {"mean_gwh": 0.0, "se_gwh": 0.0, "draws": 0}
    return out


def reweight_eue(cond_means: dict, class_probs: dict) -> float:
    """EUE (GWh per winter) under an alternative class-probability vector."""
    p = np.array([class_probs.get(c, 0.0) for c in cond_means], dtype=float)
    p = p / p.sum()
    m = np.array([cond_means[c]["mean_gwh"] for c in cond_means])
    return float((p * m).sum())
