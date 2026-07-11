"""verify_against_manuscript - assert the regenerated results match the values
reported in the manuscript. Run after scripts/run_all.py.

Exits non-zero if any check fails, so it can be used in continuous integration.
"""
import sys
from pathlib import Path
import pandas as pd

RES = Path(__file__).resolve().parents[1] / "results"

FAILS = []


def check(name, got, exp, tol):
    if abs(float(got) - float(exp)) > tol:
        FAILS.append(f"{name}: got {got}, expected {exp} (tol {tol})")


def get(df, mask, col):
    return df.loc[mask, col].iloc[0]


# --- Table 4: native REE / chi (15 GW) ---
t4 = pd.read_csv(RES / "table4_ree_by_event.csv")
for ev, c0, c3, r0, r3 in [
    ("January 2025 main", 0.239, 0.424, 515, 915),
    ("Winter Storm Elliott 2022", 0.492, 0.692, 1593, 2241),
    ("Winter Storm Uri 2021", 0.712, 0.899, 3075, 3886),
]:
    m0 = (t4.event == ev) & (t4.shock_gw == 15) & (t4.retained_gw == 0)
    m3 = (t4.event == ev) & (t4.shock_gw == 15) & (t4.retained_gw == 3)
    check(f"T4 {ev} chi R0", get(t4, m0, "chi"), c0, 0.001)
    check(f"T4 {ev} chi R3", get(t4, m3, "chi"), c3, 0.001)
    check(f"T4 {ev} REE R0", get(t4, m0, "ree_gwh"), r0, 0.6)
    check(f"T4 {ev} REE R3", get(t4, m3, "ree_gwh"), r3, 0.6)

# --- Overstatement % (full buffer) ---
ov = pd.read_csv(RES / "tableS_overstatement.csv")
for ev, q, exp in [
    ("January 2025 main", 10, 37.6), ("January 2025 main", 15, 12.6),
    ("Winter Storm Elliott 2022", 10, 10.2), ("Winter Storm Elliott 2022", 15, 4.1),
    ("Winter Storm Uri 2021", 10, 4.2), ("Winter Storm Uri 2021", 15, 2.2),
]:
    m = (ov.event == ev) & (ov.shock_gw == q) & (ov.retained_gw == 0)
    check(f"overstatement {ev} {q}GW", get(ov, m, "overstatement_pct"), exp, 0.05)

# --- Table 6: chi crossings at R=3 ---
t6 = pd.read_csv(RES / "table6_chi_crossings.csv")
for ev, exp in [("January 2025 main", 8), ("Winter Storm Elliott 2022", 4), ("Winter Storm Uri 2021", 1)]:
    m = (t6.event == ev) & (t6.retained_gw == 3)
    check(f"T6 {ev} chi>=0.10", get(t6, m, "chi>=0.1"), exp, 0)

# --- Table 7: wind shocks ---
t7 = pd.read_csv(RES / "table7_wind_shocks.csv")
for ev, a, cw, dc in [
    ("January 2025 main", 1.0, 0.455, 0.047),
    ("Winter Storm Elliott 2022", 1.0, 0.656, 0.016),
    ("Winter Storm Uri 2021", 1.0, 0.740, -0.001),
]:
    m = (t7.event == ev) & (t7.alpha == a)
    check(f"T7 {ev} chi_wind", get(t7, m, "chi_wind"), cw, 0.001)
    check(f"T7 {ev} delta", get(t7, m, "delta_chi"), dc, 0.001)

# --- Table S7: envelope shocks (100%, R=3) ---
s7 = pd.read_csv(RES / "tableS7_envelope_shocks.csv")
for ev, exp in [("January 2025 main", 0.438), ("Winter Storm Elliott 2022", 0.759), ("Winter Storm Uri 2021", 0.972)]:
    m = (s7.event == ev) & (s7.envelope_fraction == "100%")
    check(f"S7 {ev} envelope chi R3", get(s7, m, "chi_retained_3"), exp, 0.001)

# --- Table 8: documented state ---
t8 = pd.read_csv(RES / "table8_documented_state_alignment.csv")
for ev, minprc, hlt, ree in [
    ("January 2025 main", 6213, 0.0, 915),
    ("Winter Storm Elliott 2022", 4073, 0.0, 2241),
    ("Winter Storm Uri 2021", 747, 35.1, 3886),
]:
    m = t8.event == ev
    check(f"T8 {ev} min PRC", get(t8, m, "min_prc_mw"), minprc, 0.5)
    check(f"T8 {ev} hrs<EEA1", get(t8, m, "hours_equiv_prc_below_eea1"), hlt, 0.05)
    check(f"T8 {ev} REE", get(t8, m, "ree_15gw_retained3_gwh"), ree, 0.5)

# --- Uri window decomposition ---
ud = pd.read_csv(RES / "uri_window_decomposition.csv")
m0 = ud.retained_gw == 0.0
check("Uri shed share R0", get(ud, m0, "share_in_shed_pct"), 29.0, 0.1)
check("Uri EEA share R0", get(ud, m0, "share_in_eea_pct"), 40.8, 0.1)

# --- Incidence / depth ---
idp = pd.read_csv(RES / "incidence_depth.csv")
check("Uri depth", get(idp, idp.event == "Winter Storm Uri 2021", "mean_depth_gw"), 10.68, 0.01)
check("Elliott depth", get(idp, idp.event == "Winter Storm Elliott 2022", "mean_depth_gw"), 7.37, 0.01)

# --- Monte Carlo bridge ---
mc = pd.read_csv(RES / "mc_bridge_summary.csv").iloc[0]
check("MC EUE", mc["eue_gwh_per_winter"], 577, 0.5)
check("MC SE", mc["mc_standard_error_gwh"], 7, 0.5)
check("MC p95", mc["p95_gwh"], 2806, 0.5)
check("MC p99", mc["p99_gwh"], 4292, 0.5)

# --- Table 3: summary ---
t3 = pd.read_csv(RES / "table3_event_summary.csv")
for ev, peak, minprc, tight in [
    ("January 2025 main", 77537, 6213, 17),
    ("Winter Storm Elliott 2022", 73963, 4073, 146),
    ("Winter Storm Uri 2021", 69222, 747, 282),
]:
    m = t3.event == ev
    check(f"T3 {ev} peak load", get(t3, m, "peak_load_mw"), peak, 0.5)
    check(f"T3 {ev} min PRC", get(t3, m, "min_prc_mw"), minprc, 0.5)
    check(f"T3 {ev} tight hours", get(t3, m, "hours_prc_below_8gw"), tight, 0)

# --- Table S5: report anchors ---
s5 = pd.read_csv(RES / "tableS5_report_anchors.csv")
for ev, mri, shed, ratio in [
    ("Winter Storm Uri 2021", 53641, 23418, 0.382),
    ("Winter Storm Elliott 2022", 19213, 5400, 0.060),
    ("January 2025 main", 15372, 0, 0.000),
]:
    m = s5.event == ev
    check(f"S5 {ev} max res+IRR", get(s5, m, "max_res_irr_outage_mw"), mri, 0.5)
    check(f"S5 {ev} firm shed", get(s5, m, "firm_load_shed_mw"), shed, 0.5)
    check(f"S5 {ev} ratio", get(s5, m, "report_ratio"), ratio, 0.001)

# --- Table S11: outage snapshot sensitivity (main window) ---
s11 = pd.read_csv(RES / "tableS11_jan_snapshot_sensitivity.csv")
for rule, mri, env in [("Contemporaneous central", 15372, 20790), ("Latest overall", 15044, 20462)]:
    m = (s11.window == "Jan. 19-24 main") & (s11.snapshot_rule == rule)
    check(f"S11 main {rule} max res+IRR", get(s11, m, "max_res_irr_mw"), mri, 0.5)
    check(f"S11 main {rule} max env", get(s11, m, "max_all_envelope_mw"), env, 0.5)

# --- Table S12: dedup sensitivity ---
s12 = pd.read_csv(RES / "tableS12_jan_dedup_sensitivity.csv")
for rule, r0, r3 in [("Latest SCED run", 515482, 915496), ("First SCED run", 515396, 915409),
                     ("Mean within slot", 515439, 915452)]:
    m0 = (s12.deduplication_rule == rule) & (s12.retained_gw == 0.0)
    m3 = (s12.deduplication_rule == rule) & (s12.retained_gw == 3.0)
    check(f"S12 {rule} REE R0", get(s12, m0, "ree_mwh"), r0, 1.5)
    check(f"S12 {rule} REE R3", get(s12, m3, "ree_mwh"), r3, 1.5)

# --- report ---
print(f"verify_against_manuscript: {'ALL PASS' if not FAILS else 'FAILURES'} ({len(FAILS)} failing)")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
