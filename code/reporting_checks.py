"""Reporting checks for matched-pair comparisons, buffer headroom, factor widths and summary tables.

Reads results written earlier in the same run (sensitivity_surface.csv,
alternative_buffers.csv, sensitivity_ranges.csv, persistence_sensitivity.csv,
day_composition.csv, reserve_tail_summary.csv, fixed_shocks.csv,
diagnostic_windows.csv, typical_periods.csv) and the reserve panels in data/.

Outputs (all in results/):
  matched_pair_comparison.csv  pairwise counts over the 1,350 matched assumption
                               combinations (25 shocks x 2 retained reserves x
                               3 buffers x 9 endpoint-shift combinations) for all
                               ten event pairs;
  matched_pair_crossings.csv   every matched combination in which the lower-listed
                               event has the larger chi;
  buffer_headroom.csv          slot-level RTOLCAP versus PRC headroom in each
                               central window;
  factor_widths_15gw.csv       one-factor chi widths at 15 GW, including PRC versus
                               RTOLCAP alone and the 0-4 h persistence increase;
  persistence_vs_buffer_width.csv  for each of the 20 primary event/shock/retention
                               cases, the 0-4 h persistence increase compared with
                               the PRC-versus-RTOLCAP and three-buffer widths at the
                               same shock and retained reserve (central endpoints);
  reporting_summary.csv        main-text Table 13 (chi, incidence, depth and
                               observed lower-tail duration for five windows);
  native_hourly_periods.csv    diagnostic (largest-gap) and typical
                               (median-positive-gap) six-hour periods with the
                               full-event 10 GW / 0 GW overstatement;
  reporting_verification.json  assertions of the values quoted in the article.

These are descriptive comparisons of the screening calculation. They are not
probability statements, event-severity rankings or physical adequacy tests.
Run: python reporting_checks.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
O = ROOT / 'results'
KEY = ['shock_gw', 'retained_gw', 'basis', 'start_shift_h', 'end_shift_h']
ORDER = ['january_2025', 'elliott_2022', 'uri_2021', 'february_2022', 'july_2022']
PAIRS = [('january_2025', 'elliott_2022'), ('elliott_2022', 'uri_2021'), ('january_2025', 'uri_2021'),
         ('february_2022', 'elliott_2022'), ('july_2022', 'uri_2021'),
         ('january_2025', 'february_2022'), ('elliott_2022', 'july_2022'),
         ('february_2022', 'july_2022'), ('january_2025', 'july_2022'), ('february_2022', 'uri_2021')]

# ------------------------------------------------------------------ matched grid
s = pd.read_csv(O / 'sensitivity_surface.csv')
w = s.pivot_table(index=KEY, columns='event', values='chi').reset_index()
assert len(w) == 1350 and not w[ORDER].isna().any().any()
pair_rows, cross_rows = [], []
for lo, hi in PAIRS:
    d = w[hi] - w[lo]
    above = w[d < 0]
    pair_rows.append(dict(
        lower=lo, upper=hi, combinations=int(len(w)),
        lower_strictly_below=int((d > 0).sum()), ties=int((d == 0).sum()),
        lower_above_upper=int((d < 0).sum()),
        smallest_margin_upper_minus_lower=float(d.min()),
        smallest_margin_shock_ge_2gw=float(d[w.shock_gw >= 2].min()),
        tie_max_shock_gw=float(w.loc[d == 0, 'shock_gw'].max()) if (d == 0).any() else np.nan,
        ties_all_zero_chi=bool(((w.loc[d == 0, lo] == 0) & (w.loc[d == 0, hi] == 0)).all()) if (d == 0).any() else True,
        crossing_bases=';'.join(sorted(above.basis.unique())),
        crossing_end_shifts_h=';'.join(str(int(x)) for x in sorted(above.end_shift_h.unique())),
        crossing_shock_min_gw=float(above.shock_gw.min()) if len(above) else np.nan,
        crossing_shock_max_gw=float(above.shock_gw.max()) if len(above) else np.nan,
        crossings_at_15gw=int((above.shock_gw == 15).sum())))
    for _, r in above.iterrows():
        cross_rows.append(dict(lower=lo, upper=hi, **{k: r[k] for k in KEY},
                               chi_lower=float(r[lo]), chi_upper=float(r[hi]),
                               upper_minus_lower=float(r[hi] - r[lo])))
pairs = pd.DataFrame(pair_rows)
crossings = pd.DataFrame(cross_rows)
chain = ((w.january_2025 <= w.february_2022) & (w.february_2022 <= w.elliott_2022) &
         (w.elliott_2022 <= w.july_2022) & (w.july_2022 <= w.uri_2021))
original = (w.january_2025 <= w.elliott_2022) & (w.elliott_2022 <= w.uri_2021)

# ------------------------------------------------------------------ headroom
head_rows = []
for k in ORDER:
    x = pd.read_csv(DATA / f'{k}_reserve.csv')
    g = x.rtolcap_mw - x.prc_mw
    head_rows.append(dict(
        event=k, slots=int(len(x)), median_prc_mw=float(x.prc_mw.median()),
        median_rtolcap_mw=float(x.rtolcap_mw.median()), median_rtoffcap_mw=float(x.rtoffcap_mw.median()),
        median_rtolcap_minus_prc_mw=float(g.median()), mean_rtolcap_minus_prc_mw=float(g.mean()),
        min_rtolcap_minus_prc_mw=float(g.min()),
        median_slot_ratio_rtolcap_to_prc=float((x.rtolcap_mw / x.prc_mw).median()),
        share_slots_rtolcap_le_prc=float((g <= 0).mean()), share_slots_rtolcap_lt_prc=float((g < 0).mean())))
headroom = pd.DataFrame(head_rows)

# ------------------------------------------------------------------ widths
r = pd.read_csv(O / 'sensitivity_ranges.csv').set_index(['event', 'factor'])
ab = pd.read_csv(O / 'alternative_buffers.csv').set_index(['event', 'basis', 'retained_gw'])
p = pd.read_csv(O / 'persistence_sensitivity.csv')
p = p[(p.boundary_rule == 'full_horizon') & (p.shock_gw == 15) & (p.retained_gw == 3)].pivot(index='event', columns='horizon_h', values='chi')
width = lambda e, f: float(r.loc[(e, f), 'chi_max'] - r.loc[(e, f), 'chi_min'])
wid_rows = []
for k in ORDER:
    prc3, rtol3 = float(ab.loc[(k, 'PRC', 3.0), 'chi']), float(ab.loc[(k, 'RTOLCAP', 3.0), 'chi'])
    prc0, rtol0 = float(ab.loc[(k, 'PRC', 0.0), 'chi']), float(ab.loc[(k, 'RTOLCAP', 0.0), 'chi'])
    wid_rows.append(dict(
        event=k, three_buffer_width=width(k, 'three_buffer_definitions'),
        prc_vs_rtolcap_width=prc3 - rtol3, prc_vs_rtolcap_width_retained0=prc0 - rtol0,
        retention_width=width(k, 'retained_0_to_3_GW'), endpoint_width=width(k, 'nine_event_windows'),
        persistence_4h_increase=float(p.loc[k, 4] - p.loc[k, 0]),
        persistence_1h_increase=float(p.loc[k, 1] - p.loc[k, 0]),
        persistence_2h_increase=float(p.loc[k, 2] - p.loc[k, 0])))
widths = pd.DataFrame(wid_rows)

# ------------------------------------------------------------------ persistence versus buffer width, 20 cases
pf = pd.read_csv(O / 'persistence_sensitivity.csv')
pf = pf[pf.boundary_rule == 'full_horizon'].pivot_table(index=['event', 'shock_gw', 'retained_gw'], columns='horizon_h', values='chi')
cen = s[(s.start_shift_h == 0) & (s.end_shift_h == 0)].pivot_table(index=['event', 'shock_gw', 'retained_gw'], columns='basis', values='chi')
pv_rows = []
for (k, q_, R_), r_ in pf.iterrows():
    b = cen.loc[(k, float(q_), float(R_))] if (k, float(q_), float(R_)) in cen.index else cen.loc[(k, q_, R_)]
    inc = float(r_[4] - r_[0])
    pv_rows.append(dict(event=k, shock_gw=q_, retained_gw=R_, chi_native=float(r_[0]), persistence_4h_increase=inc,
                        prc_vs_rtolcap_width=float(b['PRC'] - b['RTOLCAP']),
                        three_buffer_width=float(b['PRC'] - b['RTOLCAP+RTOFFCAP']),
                        persistence_below_prc_vs_rtolcap=bool(inc < b['PRC'] - b['RTOLCAP']),
                        persistence_below_three_buffer=bool(inc < b['PRC'] - b['RTOLCAP+RTOFFCAP'])))
pvw = pd.DataFrame(pv_rows)

# ------------------------------------------------------------------ Table 13
tail = pd.read_csv(O / 'reserve_tail_summary.csv').set_index('event')
sum_rows = []
for k in ORDER:
    row = dict(event=k)
    for R in (0.0, 3.0):
        a = ab.loc[(k, 'PRC', R)]
        tag = f'retained{int(R)}'
        row[f'chi_{tag}'] = float(a.chi)
        row[f'incidence_{tag}'] = float(a.incidence)
        row[f'mean_depth_gw_{tag}'] = float(a.mean_depth_mw) / 1000
        # chi = incidence x mean depth / q for a constant shock on equal intervals
        assert abs(a.incidence * a.mean_depth_mw / 15000 - a.chi) < 1e-12, (k, R)
    for c in ('median_prc_mw', 'min_prc_mw', 'eea1_trigger_mw', 'hours_below_eea1',
              'hours_below_3000_mw', 'longest_run_below_3000_mw_h', 'chi_5gw_retained0'):
        row[c] = float(tail.loc[k, c])
    sum_rows.append(row)
summary = pd.DataFrame(sum_rows)

# ------------------------------------------------------------------ Table 9
fx = pd.read_csv(O / 'fixed_shocks.csv').set_index(['event', 'shock_gw', 'retained_gw'])
dg = pd.read_csv(O / 'diagnostic_windows.csv').set_index('event')
tp = pd.read_csv(O / 'typical_periods.csv').set_index('event')
per_rows = []
for k in ['january_2025', 'elliott_2022', 'uri_2021']:
    full = float(fx.loc[(k, 10.0, 0.0), 'overstatement_pct'])
    for kind, src, nat, hm in (('diagnostic_largest_gap', dg, 'native_gwh', 'hourly_min_gwh'),
                                ('typical_median_positive_gap', tp, 'grid_ree_gwh', 'hourly_min_ree_gwh')):
        n, h = float(src.loc[k, nat]), float(src.loc[k, hm])
        per_rows.append(dict(event=k, period=kind, start=src.loc[k, 'start'], end_exclusive=src.loc[k, 'end_exclusive'],
                             native_gwh=n, hourly_min_gwh=h, excess_pct=100 * (h - n) / n,
                             full_event_excess_pct_10gw_0gw=full))
periods = pd.DataFrame(per_rows)

# ------------------------------------------------------------------ day composition
dc = pd.read_csv(O / 'day_composition.csv').set_index(['event', 'shock_gw', 'retained_gw'])
dci = {k: (round(float(dc.loc[(k, 15.0, 3.0), 'chi_low']), 3), round(float(dc.loc[(k, 15.0, 3.0), 'chi_high']), 3)) for k in ORDER}

# ------------------------------------------------------------------ assertions of quoted values
P = pairs.set_index(['lower', 'upper'])
je, eu = P.loc[('january_2025', 'elliott_2022')], P.loc[('elliott_2022', 'uri_2021')]
fe, ju = P.loc[('february_2022', 'elliott_2022')], P.loc[('july_2022', 'uri_2021')]
jf = P.loc[('january_2025', 'february_2022')]
assert int(original.sum()) == 1350
assert (je.lower_strictly_below, je.ties, je.lower_above_upper) == (1197, 153, 0) and je.tie_max_shock_gw == 5 and je.ties_all_zero_chi
assert (eu.lower_strictly_below, eu.ties, eu.lower_above_upper) == (1350, 0, 0)
assert (ju.lower_strictly_below, ju.lower_above_upper) == (1350, 0)
# quoted as 'at least 0.0003 at 1 GW and at least 0.0038 at 2 GW or more'
assert 0.0003 <= ju.smallest_margin_upper_minus_lower < 0.0004
assert 0.0038 <= ju.smallest_margin_shock_ge_2gw < 0.0039
assert len(pairs) == 10 and pairs.ties_all_zero_chi.all()
assert int(P.lower_above_upper.sum()) == 111
assert fe.lower_above_upper == 55 and fe.crossing_bases == 'PRC' and fe.crossing_end_shifts_h == '24'
assert round(-fe.smallest_margin_upper_minus_lower, 3) == 0.028 and fe.crossings_at_15gw == 2
fc = crossings[(crossings.lower == 'february_2022') & (crossings.upper == 'elliott_2022')]
assert int((fc.start_shift_h == 24).sum()) == 47
f15 = fc[fc.shock_gw == 15]
assert set(zip(f15.start_shift_h, f15.end_shift_h)) == {(24, 24)}
f15r3 = f15[f15.retained_gw == 3].iloc[0]
assert (round(f15r3.chi_lower, 3), round(f15r3.chi_upper, 3)) == (0.705, 0.690)
assert jf.lower_above_upper == 56 and jf.crossing_bases == 'RTOLCAP;RTOLCAP+RTOFFCAP' and round(-jf.smallest_margin_upper_minus_lower, 3) == 0.003
# quoted as 'by up to approximately 0.0031' and 'by up to approximately 0.028'
assert round(-jf.smallest_margin_upper_minus_lower, 4) == 0.0031 and round(-fe.smallest_margin_upper_minus_lower, 3) == 0.028
assert int(chain.sum()) == 1239
pe = pd.read_csv(O / 'persistence_sensitivity.csv'); pe = pe[pe.boundary_rule == 'full_horizon']
pw = pe.pivot_table(index=['horizon_h', 'shock_gw', 'retained_gw'], columns='event', values='chi')
assert len(pw) == 16
assert ((pw.january_2025 <= pw.elliott_2022) & (pw.elliott_2022 <= pw.uri_2021) &
        (pw.february_2022 < pw.elliott_2022) & (pw.july_2022 < pw.uri_2021)).all()
W_ = widths.set_index('event')
assert [round(W_.loc[k, 'prc_vs_rtolcap_width'], 3) for k in ORDER] == [0.339, 0.421, 0.273, 0.582, 0.418]
assert (W_.prc_vs_rtolcap_width > W_.retention_width).all() and (W_.prc_vs_rtolcap_width > W_.endpoint_width).all()
assert round(W_.retention_width.min(), 3) == 0.185 and round(W_.retention_width.max(), 3) == 0.200
assert round(W_.endpoint_width.min(), 3) == 0.019 and round(W_.endpoint_width.max(), 3) == 0.091
assert round(W_.loc['january_2025', 'retention_width'], 3) == 0.185 and round(W_.loc['january_2025', 'three_buffer_width'], 3) == 0.409
assert round(W_.loc['january_2025', 'persistence_4h_increase'], 3) == 0.123
others = W_.drop('january_2025').persistence_4h_increase
assert (round(others.min(), 3), round(others.max(), 3)) == (0.031, 0.063)
assert (W_.persistence_4h_increase < W_.prc_vs_rtolcap_width).all()
assert W_.persistence_4h_increase.max() < W_.prc_vs_rtolcap_width.min()
H = headroom.set_index('event')
assert (round(H.median_slot_ratio_rtolcap_to_prc.min(), 2), round(H.median_slot_ratio_rtolcap_to_prc.max(), 2)) == (1.85, 2.45)
assert H.median_rtolcap_minus_prc_mw.idxmin() == 'uri_2021'
assert (H.drop('uri_2021').share_slots_rtolcap_le_prc == 0).all() and round(100 * H.loc['uri_2021', 'share_slots_rtolcap_le_prc'], 1) == 0.8
S = summary.set_index('event')
assert round(100 * S.loc['january_2025', 'incidence_retained0'], 1) == 82.2
assert (S.drop('january_2025').incidence_retained0 == 1).all() and (S.incidence_retained3 == 1).all()
assert (round(S.loc['july_2022', 'mean_depth_gw_retained3'], 2), round(S.loc['uri_2021', 'mean_depth_gw_retained3'], 2)) == (13.28, 13.49)
assert round(S.loc['elliott_2022', 'chi_retained3'] - S.loc['february_2022', 'chi_retained3'], 3) == 0.027
Q = periods.set_index(['event', 'period'])
assert [round(Q.loc[(k, 'diagnostic_largest_gap'), 'excess_pct'], 1) for k in ['january_2025', 'elliott_2022', 'uri_2021']] == [47.8, 17.2, 7.4]
assert [round(Q.loc[(k, 'typical_median_positive_gap'), 'excess_pct'], 1) for k in ['january_2025', 'elliott_2022', 'uri_2021']] == [35.5, 6.0, 2.8]
assert [round(Q.loc[(k, 'diagnostic_largest_gap'), 'full_event_excess_pct_10gw_0gw'], 1) for k in ['january_2025', 'elliott_2022', 'uri_2021']] == [37.6, 10.2, 4.2]
assert dci['february_2022'] == (0.616, 0.707) and dci['july_2022'] == (0.854, 0.916)
assert dci['elliott_2022'] == (0.624, 0.747) and dci['uri_2021'] == (0.852, 0.943)

assert len(pvw) == 20 and int(pvw.persistence_below_prc_vs_rtolcap.sum()) == 19 and int(pvw.persistence_below_three_buffer.sum()) == 19
ex = pvw[~pvw.persistence_below_prc_vs_rtolcap].iloc[0]
assert (ex.event, int(ex.shock_gw), float(ex.retained_gw)) == ('january_2025', 10, 0.0)
assert (round(ex.chi_native, 3), round(ex.persistence_4h_increase, 3), round(ex.prc_vs_rtolcap_width, 3)) == (0.043, 0.063, 0.042)
assert round(W_.three_buffer_width.min(), 3) == 0.351 and round(W_.three_buffer_width.max(), 3) == 0.649
assert (round(H.median_rtolcap_minus_prc_mw.min() / 1000, 1), round(H.median_rtolcap_minus_prc_mw.max() / 1000, 1)) == (3.2, 11.7)
# displayed cells of main Table 13 and Supplementary Tables S28 and S30
t13 = [[f'{S.loc[k, "chi_retained0"]:.3f} / {S.loc[k, "chi_retained3"]:.3f}', f'{100*S.loc[k, "incidence_retained0"]:.1f} / {100*S.loc[k, "incidence_retained3"]:.1f}',
        f'{S.loc[k, "mean_depth_gw_retained0"]:.2f} / {S.loc[k, "mean_depth_gw_retained3"]:.2f}', f'{S.loc[k, "median_prc_mw"]:,.0f} / {S.loc[k, "min_prc_mw"]:,.0f}',
        f'{S.loc[k, "hours_below_eea1"]:.1f}', f'{S.loc[k, "hours_below_3000_mw"]:.1f}', f'{S.loc[k, "longest_run_below_3000_mw_h"]:.1f}'] for k in ORDER]
assert t13 == [['0.239 / 0.424', '82.2 / 100.0', '4.35 / 6.36', '11,256 / 6,213', '0.0', '0.0', '0.0'],
               ['0.492 / 0.692', '100.0 / 100.0', '7.37 / 10.37', '7,224 / 4,073', '0.0', '0.0', '0.0'],
               ['0.712 / 0.899', '100.0 / 100.0', '10.68 / 13.49', '4,060 / 747', '35.1', '65.1', '20.3'],
               ['0.465 / 0.665', '100.0 / 100.0', '6.97 / 9.97', '8,029 / 4,500', '0.0', '0.0', '0.0'],
               ['0.686 / 0.885', '100.0 / 100.0', '10.29 / 13.28', '4,481 / 2,524', '0.0', '5.6', '3.6']], t13
s28 = [[f'{H.loc[k, "median_prc_mw"]:,.0f}', f'{H.loc[k, "median_rtolcap_mw"]:,.0f}', f'{H.loc[k, "median_rtolcap_minus_prc_mw"]:,.0f}',
        f'{H.loc[k, "median_slot_ratio_rtolcap_to_prc"]:.2f}', f'{100*H.loc[k, "share_slots_rtolcap_le_prc"]:.1f}'] for k in ORDER]
assert s28 == [['11,256', '20,739', '9,549', '1.85', '0.0'], ['7,224', '14,693', '7,310', '2.02', '0.0'], ['4,060', '7,217', '3,239', '1.86', '0.8'],
               ['8,029', '19,885', '11,707', '2.39', '0.0'], ['4,481', '11,072', '6,629', '2.45', '0.0']], s28
s30 = [[f'{W_.loc[k, c]:.3f}' for c in ('three_buffer_width', 'prc_vs_rtolcap_width', 'retention_width', 'endpoint_width', 'persistence_4h_increase')] for k in ORDER]
assert s30 == [['0.409', '0.339', '0.185', '0.091', '0.123'], ['0.582', '0.421', '0.200', '0.033', '0.063'], ['0.351', '0.273', '0.188', '0.027', '0.031'],
               ['0.649', '0.582', '0.200', '0.053', '0.057'], ['0.577', '0.418', '0.199', '0.019', '0.042']], s30
t9 = [[f'{Q.loc[(k, kind), "native_gwh"]:.3f}', f'{Q.loc[(k, kind), "hourly_min_gwh"]:.3f}'] for k in ['january_2025', 'elliott_2022', 'uri_2021']
      for kind in ('diagnostic_largest_gap', 'typical_median_positive_gap')]
assert t9 == [['5.816', '8.599'], ['2.540', '3.441'], ['11.910', '13.954'], ['24.283', '25.732'], ['32.005', '34.384'], ['36.434', '37.457']], t9

# ------------------------------------------------------------------ write
pairs.to_csv(O / 'matched_pair_comparison.csv', index=False)
crossings.to_csv(O / 'matched_pair_crossings.csv', index=False)
headroom.to_csv(O / 'buffer_headroom.csv', index=False)
widths.to_csv(O / 'factor_widths_15gw.csv', index=False)
pvw.to_csv(O / 'persistence_vs_buffer_width.csv', index=False)
summary.to_csv(O / 'reporting_summary.csv', index=False)
periods.to_csv(O / 'native_hourly_periods.csv', index=False)
report = dict(status='PASS', matched_combinations=1350, original_three_event_weak_order=int(original.sum()),
              five_window_chain_holds=int(chain.sum()), feb_above_elliott=int(fe.lower_above_upper),
              july_above_uri=int(ju.lower_above_upper), january_above_february=int(jf.lower_above_upper),
              persistence_grid_cases=int(len(pw)), persistence_below_buffer_width_cases=int(pvw.persistence_below_prc_vs_rtolcap.sum()),
              day_composition_chi_15gw_3gw=dci,
              scope='Descriptive comparisons of the screening calculation; not probability statements, '
                    'event-severity rankings or physical adequacy tests.')
(O / 'reporting_verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(pairs.round(4).to_string(index=False))
print(widths.round(3).to_string(index=False))
print(headroom.round(3).to_string(index=False))
print(summary.round(3).to_string(index=False))
print(periods.round(3).to_string(index=False))
print(json.dumps(report, indent=2))
