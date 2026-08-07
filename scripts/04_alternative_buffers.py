"""04 - Alternative operating-buffer definitions.

Regenerates:
  results/tableS8_alternative_buffers.csv (Supplementary S8: chi under PRC / RTOLCAP / RTOLCAP+RTOFFCAP)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import io, estimator, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)

BUFFERS = ["PRC", "RTOLCAP", "RTOLCAP+RTOFFCAP"]


def alt_buffers():
    rows = []
    for ev in C.EVENT_ORDER:
        iv = io.load_interval_reserve(ev)
        for b in BUFFERS:
            base = estimator.buffer_series(iv, 0, b)
            r0 = estimator.ree_native(iv, 15000, 0, buffer=b)["chi"]
            r3 = estimator.ree_native(iv, 15000, 3000, buffer=b)["chi"]
            rows.append({
                "event": C.EVENTS[ev]["label"], "buffer": b,
                "min_buffer_mw": round(float(np.min(base))),
                "chi_retained_0": round(r0, 3),
                "chi_retained_3": round(r3, 3),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    alt_buffers().to_csv(RES / "tableS8_alternative_buffers.csv", index=False)
    print("04: wrote tableS8_alternative_buffers.csv")
