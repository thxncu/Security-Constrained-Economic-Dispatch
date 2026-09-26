"""Summarize the level and lower tail of each central PRC path (Section 5.6).

For each of the five central windows this reports the median and minimum
five-minute PRC, the hours with PRC below the EEA1 trigger in force (2,500 MW for
January 2025, 2,300 MW otherwise), the hours below 3,000 MW (ERCOT's low-reserve
boundary), the longest consecutive run below 3,000 MW, and chi for a 5 GW shock
with no retained reserve and a 15 GW shock with 3 GW retained. Each slot counts
1/12 h. The flagged July 12, 2022 17:40 slot keeps its interpolated value
(4,033.725 MW), which lies above both thresholds.

The chi values are recomputed here and, when results/sensitivity_surface.csv
from analyze_r3.py is present, must match it. The script also asserts the
July-versus-Uri comparison quoted in the main text.
Run: python reserve_tail_summary.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DT = 1 / 12
LOW = 3000.0
events = json.loads((DATA / "events.json").read_text())

def chi(prc, shock_mw, retained_mw):
    buffer = np.maximum(prc - retained_mw, 0.0)
    return float(np.maximum(shock_mw - buffer, 0.0).sum() / (shock_mw * len(prc)))

def longest_run(mask):
    best = run = 0
    for flag in mask:
        run = run + 1 if flag else 0
        best = max(best, run)
    return best

rows = []
for key, (start, end, year, label) in events.items():
    panel = pd.read_csv(DATA / f"{key}_reserve.csv", parse_dates=["slot"])
    prc = panel["prc_mw"].to_numpy(float)
    trigger = 2500.0 if key == "january_2025" else 2300.0
    rows.append({
        "event": key, "slots": int(len(prc)), "imputed_slots": int(panel["imputed"].astype(bool).sum()),
        "min_prc_mw": float(prc.min()), "median_prc_mw": float(np.median(prc)),
        "eea1_trigger_mw": trigger,
        "hours_below_eea1": float((prc < trigger).sum() * DT),
        "hours_below_3000_mw": float((prc < LOW).sum() * DT),
        "longest_run_below_3000_mw_h": float(longest_run(prc < LOW) * DT),
        "chi_5gw_retained0": chi(prc, 5000.0, 0.0),
        "chi_15gw_retained3": chi(prc, 15000.0, 3000.0),
    })
table = pd.DataFrame(rows)

surface = ROOT / "results" / "sensitivity_surface.csv"
cross_checked = False
if surface.is_file():
    s = pd.read_csv(surface)
    s = s[(s["basis"] == "PRC") & (s["start_shift_h"] == 0) & (s["end_shift_h"] == 0)]
    for _, r in table.iterrows():
        for q, ret, col in ((5, 0.0, "chi_5gw_retained0"), (15, 3.0, "chi_15gw_retained3")):
            ref = s[(s["event"] == r["event"]) & (s["shock_gw"] == q) & (s["retained_gw"] == ret)]["chi"]
            assert len(ref) == 1 and abs(float(ref.iloc[0]) - r[col]) <= 1e-12, (r["event"], q, ret)
    cross_checked = True

t = table.set_index("event")
jul, uri = t.loc["july_2022"], t.loc["uri_2021"]
assert round(jul["median_prc_mw"]) == 4481 and round(uri["median_prc_mw"]) == 4060
assert round(jul["hours_below_eea1"], 1) == 0.0 and round(uri["hours_below_eea1"], 1) == 35.1
assert round(jul["hours_below_3000_mw"], 1) == 5.6 and round(uri["hours_below_3000_mw"], 1) == 65.1
assert round(jul["longest_run_below_3000_mw_h"], 1) == 3.6 and round(uri["longest_run_below_3000_mw_h"], 1) == 20.3
assert round(jul["chi_5gw_retained0"], 3) == 0.135 and round(uri["chi_5gw_retained0"], 3) == 0.224
assert round(jul["chi_15gw_retained3"], 3) == 0.885 and round(uri["chi_15gw_retained3"], 3) == 0.899

(ROOT / "results").mkdir(exist_ok=True)
table.to_csv(ROOT / "results" / "reserve_tail_summary.csv", index=False)
report = {"status": "PASS", "events": int(len(table)), "chi_cross_checked_against_sensitivity_surface": cross_checked,
          "scope": "Descriptive level and lower-tail duration of observed PRC; not a physical adequacy test."}
(ROOT / "results" / "reserve_tail_verification.json").write_text(json.dumps(report, indent=2))
print(table.round(3).to_string(index=False))
print(json.dumps(report, indent=2))
