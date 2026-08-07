"""03 - Event-specific envelope shocks and time-varying wind-derating shocks.

Regenerates:
  results/table7_wind_shocks.csv          (main Table 7: wind-shaped vs equal-energy)
  results/tableS7_envelope_shocks.csv     (Supplementary S7: envelope shocks 50% / 100%)
  results/tableS16_wind_buffer_alignment.csv (2nd-revision addition: shock-buffer
                                          alignment behind the Table 7 timing sign)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, shocks, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)


def wind_shocks():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for a in C.WIND_ALPHAS:
            traj = shocks.wind_derating_trajectory(ev, a, iv)
            rw = estimator.ree_native(iv, traj, 3000)
            geq = shocks.equal_energy_constant_gw(traj)
            rc = estimator.ree_native(iv, geq * 1000.0, 3000)
            rows.append({
                "event": C.EVENTS[ev]["label"], "alpha": a,
                "total_shock_energy_gwh": round(traj.sum() * C.INTERVAL_HOURS / 1000.0),
                "chi_wind": round(rw["chi"], 3),
                "equal_energy_constant_gw": round(geq, 2),
                "chi_constant": round(rc["chi"], 3),
                "delta_chi": round(rw["chi"] - rc["chi"], 3),
            })
    return pd.DataFrame(rows)


def envelope_shocks():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for frac in [0.5, 1.0]:
            q = shocks.envelope_shock_mw(ev, frac)
            r0 = estimator.ree_native(iv, q, 0)["chi"]
            r3 = estimator.ree_native(iv, q, 3000)["chi"]
            rows.append({
                "event": C.EVENTS[ev]["label"],
                "envelope_fraction": f"{int(frac*100)}%",
                "shock_gw": round(q / 1000.0, 2),
                "chi_retained_0": round(r0, 3),
                "chi_retained_3": round(r3, 3),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    wind_shocks().to_csv(RES / "table7_wind_shocks.csv", index=False)
    envelope_shocks().to_csv(RES / "tableS7_envelope_shocks.csv", index=False)
    print("03: wrote table7_wind_shocks.csv, tableS7_envelope_shocks.csv")


# ---------------------------------------------------------------------------
# 2nd-revision addition: shock-buffer alignment behind the Table 7 timing sign
# (Corollary 1, Section 3.4). Emitted as Supplementary Table S16.
# ---------------------------------------------------------------------------
def _alignment_table():
    from ree import bootstrap
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        w = shocks.wind_derating_trajectory(ev, 1.0, iv)
        for r in C.CENTRAL_RETAINED_GW:
            B = np.maximum(iv["prc_mw"].to_numpy(dtype=float) - r * 1000.0, 0.0)
            a = bootstrap.shock_buffer_alignment(w, B)
            rows.append({"event": C.EVENTS[ev]["label"], "retained_gw": r,
                         "pearson_shock_buffer": round(a["pearson"], 3),
                         "spearman_shock_buffer": round(a["spearman"], 3)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    _alignment_table().to_csv(C.RESULTS_DIR / "tableS16_wind_buffer_alignment.csv", index=False)
    print("03b: wrote tableS16_wind_buffer_alignment.csv")
