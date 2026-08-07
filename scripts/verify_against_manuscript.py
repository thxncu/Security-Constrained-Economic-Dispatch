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

# --- 2nd-revision additions ---

# Table S13: day-block bootstrap intervals (seeded, so exactly reproducible).
s13 = pd.read_csv(RES / "tableS13_block_bootstrap_ci.csv")
for ev, g, r, clo, chi_hi in [
    ("January 2025 main", 15, 0, 0.182, 0.297),
    ("January 2025 main", 15, 3, 0.356, 0.495),
    ("Winter Storm Elliott 2022", 15, 3, 0.624, 0.747),
    ("Winter Storm Uri 2021", 15, 3, 0.852, 0.943),
]:
    m = (s13.event == ev) & (s13.shock_gw == g) & (s13.retained_gw == r)
    check(f"S13 {ev} {g}GW R{r} chi lo", get(s13, m, "chi_ci95_lo"), clo, 0.001)
    check(f"S13 {ev} {g}GW R{r} chi hi", get(s13, m, "chi_ci95_hi"), chi_hi, 0.001)
# ordering separation at 15 GW: adjacent-event chi intervals must not overlap
for r in (0, 3):
    sub = s13[(s13.shock_gw == 15) & (s13.retained_gw == r)].set_index("event")
    jan_hi = sub.loc["January 2025 main", "chi_ci95_hi"]
    ell_lo = sub.loc["Winter Storm Elliott 2022", "chi_ci95_lo"]
    ell_hi = sub.loc["Winter Storm Elliott 2022", "chi_ci95_hi"]
    uri_lo = sub.loc["Winter Storm Uri 2021", "chi_ci95_lo"]
    if not (jan_hi < ell_lo and ell_hi < uri_lo):
        FAILS.append(f"S13 ordering separation violated at retained {r} GW")

# Table S14: numerical convexity check must pass for every event/retained case.
s14 = pd.read_csv(RES / "tableS14_convexity_check.csv")
if not s14["convex_up_to_float_error"].all():
    FAILS.append("S14 convexity check failed")

# Table S15: mixture reweighting (baseline must match published bridge within MC error).
s15 = pd.read_csv(RES / "tableS15_mc_prob_sensitivity.csv")
base = s15[s15.probability_vector.str.startswith("Baseline")]
check("S15 baseline reweighted EUE", base["eue_gwh_per_winter"].iloc[0], 574, 0.5)
for label, exp in [("Event classes half as frequent", 287), ("1.5x as frequent", 861),
                   ("Uri class half as frequent", 473)]:
    row = s15[s15.probability_vector.str.contains(label)]
    check(f"S15 {label}", row["eue_gwh_per_winter"].iloc[0], exp, 0.5)

# Table S16: shock-buffer alignment must be monotone in the event ordering and
# must move opposite to the Table 7 timing penalty.
s16 = pd.read_csv(RES / "tableS16_wind_buffer_alignment.csv")
a = s16[s16.retained_gw == 3].set_index("event")["spearman_shock_buffer"]
check("S16 Jan alignment", a["January 2025 main"], 0.035, 0.002)
check("S16 Elliott alignment", a["Winter Storm Elliott 2022"], 0.457, 0.002)
check("S16 Uri alignment", a["Winter Storm Uri 2021"], 0.663, 0.002)
if not (a["January 2025 main"] < a["Winter Storm Elliott 2022"] < a["Winter Storm Uri 2021"]):
    FAILS.append("S16 alignment ordering violated")
d = t7[t7.alpha == 1.0].set_index("event")["delta_chi"]
if not (d["January 2025 main"] > d["Winter Storm Elliott 2022"] > d["Winter Storm Uri 2021"]):
    FAILS.append("S16/T7 timing-penalty ordering does not mirror alignment ordering")

# Runtime report must exist and contain a TOTAL row and environment rows.
rt = pd.read_csv(RES / "runtime_report.csv")
if "TOTAL" not in set(rt["item"]):
    FAILS.append("runtime_report.csv missing TOTAL row")
if not (rt["kind"] == "environment").any():
    FAILS.append("runtime_report.csv missing environment rows")

# --- report ---
print(f"verify_against_manuscript: {'ALL PASS' if not FAILS else 'FAILURES'} ({len(FAILS)} failing)")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
