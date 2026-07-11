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
