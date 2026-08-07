"""13 - Day-composition bootstrap intervals and convexity verification
(2nd-revision additions for Reviewer 1).

Regenerates:
  results/tableS13_block_bootstrap_ci.csv   (REE and chi with 95% day-block
                                             percentile intervals; central
                                             shocks x retained cases)
  results/tableS14_convexity_check.csv      (numerical second-difference check
                                             of the convexity of REE in q)

Interpretation note: the intervals quantify day-composition uncertainty of the
conditional event-window estimate. They are not confidence intervals for a
population adequacy metric; that role belongs to the Eq. (3) bridge.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, bootstrap, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def bootstrap_table():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for g in C.FIXED_SHOCKS_GW:
            for r in C.CENTRAL_RETAINED_GW:
                out = bootstrap.bootstrap_ree_chi(iv, g * 1000.0, r * 1000.0)
                rows.append({
                    "event": C.EVENTS[ev]["label"],
                    "shock_gw": g, "retained_gw": r,
                    "ree_gwh": round(out["ree_gwh"], 1),
                    "ree_ci95_lo_gwh": round(out["ree_lo_gwh"], 1),
                    "ree_ci95_hi_gwh": round(out["ree_hi_gwh"], 1),
                    "chi": round(out["chi"], 3),
                    "chi_ci95_lo": round(out["chi_lo"], 3),
                    "chi_ci95_hi": round(out["chi_hi"], 3),
                    "n_days": out["n_days"], "bootstrap_reps": out["reps"],
                })
    return pd.DataFrame(rows)


def convexity_table():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for r in C.CENTRAL_RETAINED_GW:
            out = bootstrap.convexity_second_differences(iv, r * 1000.0)
            rows.append({
                "event": C.EVENTS[ev]["label"], "retained_gw": r,
                "q_grid_points": out["grid_points"],
                "min_second_difference_mwh": out["min_second_difference_mwh"],
                "convex_up_to_float_error": out["convex_up_to_float_error"],
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    bt = bootstrap_table()
    bt.to_csv(RES / "tableS13_block_bootstrap_ci.csv", index=False)
    cv = convexity_table()
    cv.to_csv(RES / "tableS14_convexity_check.csv", index=False)
    ok = cv["convex_up_to_float_error"].all()
    print(f"13: wrote tableS13_block_bootstrap_ci.csv ({len(bt)} rows), "
          f"tableS14_convexity_check.csv (all convex: {ok})")
