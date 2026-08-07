"""run_all - regenerate every table and figure from the derived panels.

Runs all numbered scripts in order. Each script is standalone and can also be
run individually. Outputs land in results/ and figures/.

2nd-revision addition (Reviewer 1, round 2): the runner now records the wall
time of every step and the execution environment, and writes them to
results/runtime_report.csv so that the manuscript can report computational cost.
"""
import platform
import runpy
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
STEPS = [
    "09_event_summary_audit.py",
    "01_reserve_exceedance_tables.py",
    "02_shock_sweep_and_crossings.py",
    "03_event_specific_and_wind_shocks.py",
    "04_alternative_buffers.py",
    "05_documented_state_alignment.py",
    "06_mechanism_decomposition.py",
    "07_montecarlo_bridge.py",
    "08_consistency_checks.py",
    "10_supplementary_tables.py",
    "11_supplementary_figures.py",
    "12_workflow_figure.py",
    "13_bootstrap_ci.py",
]


def _env_rows():
    import numpy, pandas, matplotlib, sklearn
    return [
        ("environment", "python", platform.python_version()),
        ("environment", "platform", f"{platform.system()} {platform.release()} ({platform.machine()})"),
        ("environment", "numpy", numpy.__version__),
        ("environment", "pandas", pandas.__version__),
        ("environment", "matplotlib", matplotlib.__version__),
        ("environment", "scikit-learn", sklearn.__version__),
        ("environment", "run_timestamp_utc", datetime.now(timezone.utc).isoformat(timespec="seconds")),
    ]


if __name__ == "__main__":
    rows = []
    t_all = time.perf_counter()
    for s in STEPS:
        print(f"\n>>> running {s}")
        t0 = time.perf_counter()
        runpy.run_path(str(HERE / s), run_name="__main__")
        rows.append(("step", s, f"{time.perf_counter() - t0:.2f}"))
    rows.append(("step", "TOTAL", f"{time.perf_counter() - t_all:.2f}"))
    rows += _env_rows()

    RESULTS.mkdir(exist_ok=True)
    import pandas as pd
    pd.DataFrame(rows, columns=["kind", "item", "value_seconds_or_version"]).to_csv(
        RESULTS / "runtime_report.csv", index=False)
    print("\nrun_all: complete. See results/ (incl. runtime_report.csv) and figures/.")
