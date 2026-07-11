"""Reserve-scarcity internal coherence checks (Section 6.3 / Supplementary S4).

Compares the 15 GW REE residual against RTORDPA-based reserve-scarcity labels on the
January 2025 interval panel. Because both quantities derive from the same SCED reserve
panel, this is an internal coherence check rather than independent validation.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

from . import io, config as C


def _top_k_recall(y, s, frac=0.10):
    n = max(1, int(np.ceil(frac * len(s))))
    top = np.argpartition(s, -n)[-n:]
    return float(y[top].sum() / y.sum()) if y.sum() > 0 else float("nan")


def _point_metrics(y, s):
    y = y.astype(int)
    return (float(roc_auc_score(y, s)), float(average_precision_score(y, s)),
            _top_k_recall(y, s), int(y.sum()))


def consistency_table(shock_mw: float = 15000, retained_mw: float = 3000,
                      seed: int = C.CONSISTENCY_SEED, bootstrap: int = C.CONSISTENCY_BOOTSTRAP) -> pd.DataFrame:
    """AUC / AP / top-10% recall for two scores (REE residual, load-only) against two
    labels (RTORDPA>0, RTORDPA>10), with hour-block bootstrap confidence intervals."""
    iv = io.load_interval_reserve("january_2025").copy()
    iv["hour"] = iv["slot"].dt.floor("h")
    buf = np.maximum(iv["prc_mw"].to_numpy() - retained_mw, 0.0)
    iv["score_ree"] = np.maximum(shock_mw - buf, 0.0)
    # load-only baseline: use hourly load broadcast to intervals (from the hourly panel)
    h = io.load_hourly_panel("january_2025")[["hour", "load_mw"]]
    iv = iv.merge(h, on="hour", how="left")
    iv["score_load"] = iv["load_mw"].to_numpy()
    iv["lab0"] = (iv["rtordpa"] > 0).to_numpy()
    iv["lab10"] = (iv["rtordpa"] > 10).to_numpy()

    rng = np.random.default_rng(seed)
    hours = iv["hour"].drop_duplicates().sort_values().to_numpy()
    idx_by_hour = [iv.index[iv["hour"] == hh].to_numpy() for hh in hours]
    H = len(idx_by_hour)

    def ci(label_col, score_col):
        y_all = iv[label_col].astype(int).to_numpy()
        s_all = iv[score_col].to_numpy()
        aucs, aps, recs = [], [], []
        for _ in range(bootstrap):
            samp = rng.integers(0, H, size=H)
            idx = np.concatenate([idx_by_hour[i] for i in samp])
            y, s = y_all[idx], s_all[idx]
            if 0 < y.sum() < len(y):
                aucs.append(roc_auc_score(y, s))
                aps.append(average_precision_score(y, s))
                recs.append(_top_k_recall(y, s))
        pct = lambda v: np.percentile(v, [2.5, 97.5]).tolist()
        return pct(aucs), pct(aps), pct(recs), len(aucs)

    rows = []
    for lname, lcol in [("RTORDPA>0", "lab0"), ("RTORDPA>10", "lab10")]:
        for sname, scol in [("15 GW REE residual", "score_ree"), ("Load only", "score_load")]:
            auc, ap, rec, pos = _point_metrics(iv[lcol], iv[scol])
            ca, cp, cr, nb = ci(lcol, scol)
            rows.append({
                "Label": lname, "Score": sname, "Positive intervals": pos,
                "AUC": auc, "AUC_CI_low": ca[0], "AUC_CI_high": ca[1],
                "AP": ap, "AP_CI_low": cp[0], "AP_CI_high": cp[1],
                "Top10_recall": rec, "Top10_CI_low": cr[0], "Top10_CI_high": cr[1],
                "bootstrap": "hour-block", "n_bootstrap": nb,
            })
    return pd.DataFrame(rows)
