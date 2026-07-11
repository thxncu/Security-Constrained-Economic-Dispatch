"""run_all - regenerate every table and figure from the derived panels.

Runs scripts 01-09 in order. Each script is standalone and can also be run individually.
Outputs land in results/ and figures/.
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
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
]

if __name__ == "__main__":
    for s in STEPS:
        print(f"\n>>> running {s}")
        runpy.run_path(str(HERE / s), run_name="__main__")
    print("\nrun_all: complete. See results/ and figures/.")
