"""Reconstruct included reserve panels from the extracted source executions.

This verifies the last-execution, five-minute and single-gap rules; it is not
an independent download or a check of omitted raw-source records.
Run: python verify_panels.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
COLUMNS = ["prc_mw", "rtolcap_mw", "rtoffcap_mw", "rtordpa"]
report = []
for key, (a, b, year, label) in json.loads((DATA / "events.json").read_text()).items():
    raw = pd.read_csv(DATA / f"{key}_selected_runs.csv", parse_dates=["stamp"])
    if raw["repeat"].fillna("N").ne("N").any():
        raise ValueError(f"{key}: repeated-clock handling must be explicit")
    raw["slot"] = raw["stamp"].dt.floor("5min")
    raw = raw.sort_values(["stamp", "batch"], kind="stable")
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    grid = pd.date_range(a - pd.Timedelta(days=1), b + pd.Timedelta(days=1),
                         freq="5min", inclusive="left")
    values = raw.drop_duplicates("slot", keep="last").set_index("slot")[COLUMNS].reindex(grid)
    missing = values.isna().any(axis=1)
    expected = [pd.Timestamp("2022-07-12 17:40")] if key == "july_2022" else []
    assert list(grid[missing]) == expected, (key, list(grid[missing]))
    values = values.interpolate(method="time", limit=1, limit_area="inside")
    maximum = 0.0
    for suffix, frame in [("_extended", values), ("", values.loc[(values.index >= a) & (values.index < b)])]:
        saved = pd.read_csv(DATA / f"{key}_reserve{suffix}.csv", parse_dates=["slot"]).set_index("slot")
        assert saved.index.equals(frame.index), key
        delta = np.abs(saved[COLUMNS].to_numpy() - frame.to_numpy())
        assert np.allclose(saved[COLUMNS], frame, rtol=0, atol=1e-7), (key, delta.max())
        assert saved["imputed"].to_numpy().tolist() == missing.reindex(frame.index).tolist(), key
        maximum = max(maximum, float(delta.max()))
    report.append({"event": key, "source_executions_with_margins": len(raw),
                   "missing_slots": len(expected), "max_absolute_difference_mw": maximum})
output = {"status": "PASS", "scope": "included extracted source executions", "events": report}
(ROOT / "results" / "source_execution_verification.json").write_text(json.dumps(output, indent=2))
print(json.dumps(output, indent=2))
