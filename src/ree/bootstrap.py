"""Day-block bootstrap for the conditional REE screen (2nd-revision addition).

Motivation (Reviewer 1, round 2): the screen is deterministic by design, so the
relevant uncertainty statement is not a population-sampling claim. What can be
quantified is the sensitivity of the conditional estimate to the within-event
day composition: resampling whole event days with replacement preserves the
strong intraday autocorrelation of the five-minute reserve trajectory while
varying which day-level reserve regimes enter the window.

The resulting percentile intervals are therefore reported as *day-composition
intervals* for the conditional (event-window) REE and chi. They are not
confidence intervals for a population EUE; that object belongs to the Eq. (3)
bridge and is handled in ``montecarlo``.

The day-block scheme is identical to the one already used inside the Monte
Carlo bridge, so the two additions share one resampling convention.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from . import config as C

BOOT_SEED = 20260
BOOT_REPS = 2000


def day_blocks(interval: pd.DataFrame, retained_mw: float) -> list[np.ndarray]:
    """Split the usable buffer B = max(PRC - retained, 0) into per-day arrays."""
    B = np.maximum(interval["prc_mw"].to_numpy(dtype=float) - retained_mw, 0.0)
    days = interval["slot"].dt.floor("D")
    return [B[(days == d).to_numpy()] for d in days.unique()]


def bootstrap_ree_chi(interval: pd.DataFrame, shock_mw: float, retained_mw: float,
                      reps: int = BOOT_REPS, seed: int = BOOT_SEED) -> dict:
    """Day-block bootstrap distribution of conditional REE (GWh) and chi.

    Each replicate resamples the event's days with replacement, concatenates the
    per-day buffer arrays, and re-evaluates Eqs. (1)-(2) under the same shock.
    Exposure is recomputed per replicate so chi remains well defined even if the
    resampled window length differs (it does not when all days are complete).

    Returns point estimates and 2.5/97.5 percentile bounds.
    """
    rng = np.random.default_rng(seed)
    blocks = day_blocks(interval, retained_mw)
    n_days = len(blocks)

    # point estimate on the observed window
    B_obs = np.concatenate(blocks)
    exceed = np.maximum(shock_mw - B_obs, 0.0)
    ree_pt = exceed.sum() * C.INTERVAL_HOURS / 1000.0          # GWh
    chi_pt = exceed.sum() / (shock_mw * len(B_obs)) if len(B_obs) else 0.0

    ree_b = np.empty(reps)
    chi_b = np.empty(reps)
    for r in range(reps):
        idx = rng.integers(0, n_days, size=n_days)
        Bb = np.concatenate([blocks[i] for i in idx])
        exc = np.maximum(shock_mw - Bb, 0.0)
        ree_b[r] = exc.sum() * C.INTERVAL_HOURS / 1000.0
        chi_b[r] = exc.sum() / (shock_mw * len(Bb))

    lo, hi = np.percentile(ree_b, [2.5, 97.5])
    clo, chi_hi = np.percentile(chi_b, [2.5, 97.5])
    return {
        "ree_gwh": float(ree_pt), "ree_lo_gwh": float(lo), "ree_hi_gwh": float(hi),
        "ree_boot_mean_gwh": float(ree_b.mean()),
        "chi": float(chi_pt), "chi_lo": float(clo), "chi_hi": float(chi_hi),
        "n_days": n_days, "reps": reps,
    }


def convexity_second_differences(interval: pd.DataFrame, retained_mw: float,
                                 q_lo_gw: float = 0.5, q_hi_gw: float = 25.0,
                                 step_gw: float = 0.5) -> dict:
    """Numerical check of the convexity of REE in the shock magnitude q.

    REE(q) = sum_i max(q - B_i, 0) * dt is a nonnegative sum of convex functions
    of q and is therefore convex (manuscript proposition). This helper evaluates
    REE on a uniform q grid and returns the minimum discrete second difference,
    which must be nonnegative up to floating-point error.
    """
    B = np.maximum(interval["prc_mw"].to_numpy(dtype=float) - retained_mw, 0.0)
    qs = np.arange(q_lo_gw, q_hi_gw + 1e-9, step_gw) * 1000.0
    ree = np.array([np.maximum(q - B, 0.0).sum() * C.INTERVAL_HOURS for q in qs])
    d2 = ree[2:] - 2.0 * ree[1:-1] + ree[:-2]
    return {
        "grid_points": int(len(qs)),
        "min_second_difference_mwh": float(d2.min()),
        "convex_up_to_float_error": bool(d2.min() >= -1e-6),
    }


# ----------------------------------------------------------------------------
# Shock-buffer alignment (2nd-revision addition, Corollary 1 of Section 3.4).
#
# Convexity implies that a time-varying shock is weakly worse than its
# equal-energy constant counterpart when the buffer is constant. When the buffer
# varies, the inequality can reverse if the shock is concentrated in intervals
# that carry more headroom. The rank correlation between the shock trajectory and
# the buffer trajectory measures exactly that alignment, so it predicts the sign
# of the timing penalty reported in Table 7.
# ----------------------------------------------------------------------------
def _rank(x: np.ndarray) -> np.ndarray:
    """Average ranks, so ties do not bias the rank correlation."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1, dtype=float)
    # average ties
    s = pd.Series(x)
    return s.rank(method="average").to_numpy()


def shock_buffer_alignment(shock_mw: np.ndarray, buffer_mw: np.ndarray) -> dict:
    """Pearson and Spearman correlation between a shock and a buffer trajectory."""
    q = np.asarray(shock_mw, dtype=float)
    B = np.asarray(buffer_mw, dtype=float)
    pear = float(np.corrcoef(q, B)[0, 1])
    spear = float(np.corrcoef(_rank(q), _rank(B))[0, 1])
    return {"pearson": pear, "spearman": spear}
