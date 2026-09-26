"""Check the case-selection statements for the added 2022 windows (Section 4).

Input: data/prc_daily_2022.csv, the daily minimum of five-minute PRC for every
2022 operating day, derived from the same 2022 SCED reserve workbook and the
same latest-execution rule as the event panels. Slots in the November 6 repeated
hour are kept separately by their repeated-hour flag.

The script (1) checks full-year coverage, (2) confirms that the daily file agrees
exactly with the observed slots of the February, July and December 2022 event
panels on every overlapping day, and (3) recomputes the selection statements:
July 13 is the lowest-PRC day of 2022, the lowest winter minima fall on January
30-31 (about 3.1 GW), and the February window minimum is higher than both.
Run: python selection_check.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
daily = pd.read_csv(DATA / "prc_daily_2022.csv", dtype={"date": str, "min_slot_repeated_hour": str})
events = json.loads((DATA / "events.json").read_text())

# 1. Coverage: one row per 2022 operating day.
dates = pd.to_datetime(daily["date"])
assert daily["date"].is_unique and len(daily) == 365, len(daily)
assert (dates.dt.year == 2022).all()
assert daily["observed_slots"].between(276, 300).all()
assert np.isfinite(daily["min_prc_mw"]).all()
daily = daily.set_index("date")

# 2. Agreement with the observed (non-imputed) slots of the 2022 event panels.
compared = []
for key in ("february_2022", "july_2022", "elliott_2022"):
    panel = pd.read_csv(DATA / f"{key}_reserve_extended.csv", parse_dates=["slot"])
    panel = panel[~panel["imputed"].astype(bool)]
    by_day = panel.groupby(panel["slot"].dt.strftime("%Y-%m-%d"))["prc_mw"].min()
    diff = np.abs(by_day.to_numpy() - daily.loc[by_day.index, "min_prc_mw"].to_numpy())
    assert np.all(diff <= 1e-6), (key, float(diff.max()))
    compared.append({"event": key, "days": int(len(by_day)), "max_absolute_difference_mw": float(diff.max())})

# 3. Selection statements.
def window_min(key):
    a, b = (pd.Timestamp(x) for x in events[key][:2])
    days = [d for d in daily.index if a <= pd.Timestamp(d) < b]
    return daily.loc[days, "min_prc_mw"].idxmin()

ranked = daily.sort_values(["min_prc_mw", "min_slot"])
winter = ranked[pd.to_datetime(ranked.index).month.isin([1, 2, 12])]
rows = []
for i, d in enumerate(ranked.index[:5], 1):
    rows.append(("annual_lowest_rank_%d" % i, d))
for i, d in enumerate(winter.index[:3], 1):
    rows.append(("winter_lowest_rank_%d" % i, d))
for key in ("february_2022", "july_2022", "elliott_2022"):
    rows.append((f"{key}_window_minimum", window_min(key)))
table = pd.DataFrame([{"statistic": s, "date": d,
                       "min_prc_mw": float(daily.loc[d, "min_prc_mw"]),
                       "min_slot": daily.loc[d, "min_slot"],
                       "slots_below_3500_mw": int(daily.loc[d, "slots_below_3500_mw"])} for s, d in rows])

top = ranked.index[0]
assert top == "2022-07-13" and round(daily.loc[top, "min_prc_mw"]) == 2524, (top, daily.loc[top, "min_prc_mw"])
assert window_min("july_2022") == top
assert set(winter.index[:2]) == {"2022-01-30", "2022-01-31"}, list(winter.index[:3])
assert round(winter["min_prc_mw"].iloc[0] / 1000, 1) == 3.1
feb = daily.loc[window_min("february_2022"), "min_prc_mw"]
assert feb > winter["min_prc_mw"].iloc[0], (feb, winter["min_prc_mw"].iloc[0])

(ROOT / "results").mkdir(exist_ok=True)
table.to_csv(ROOT / "results" / "selection_check.csv", index=False)
report = {"status": "PASS", "days": int(len(daily)), "panel_agreement": compared,
          "lowest_day_2022": top, "lowest_day_min_prc_mw": float(daily.loc[top, "min_prc_mw"]),
          "lowest_winter_days": list(winter.index[:2]),
          "february_window_min_prc_mw": float(feb),
          "scope": "Selection statements for the added 2022 windows; not an event census or a probability estimate."}
(ROOT / "results" / "selection_verification.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
