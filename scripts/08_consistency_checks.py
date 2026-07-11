"""08 - Reserve-scarcity internal coherence check (Section 6.3 / Supplementary S4).

Regenerates:
  results/tableS6_scarcity_consistency.csv (AUC/AP/top-10% recall with hour-block bootstrap CIs)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ree import consistency, config as C

RES = C.RESULTS_DIR
RES.mkdir(exist_ok=True)

if __name__ == "__main__":
    df = consistency.consistency_table()
    df.to_csv(RES / "tableS6_scarcity_consistency.csv", index=False)
    print("08: wrote tableS6_scarcity_consistency.csv")
