# Numerical output map

The code retains the existing result filenames to make published quantities
findable. Full-precision CSV values, rather than a pre-rounded document cell,
are authoritative for numerical comparisons.

| Output | Calculation |
|---|---|
| `fixed_shocks.csv`, `event_summary.csv` | Five central windows, 10/15 GW shocks and 0/3 GW retained reserve; data coverage and context. |
| `wind_shocks.csv` | Half/full hourly wind-loss profiles, their equal-energy constant shocks and correlations. |
| `day_composition.csv`, `convexity.csv` | Whole-day resampling and the scalar-grid convexity check. |
| `sensitivity_surface.csv`, `window_sensitivity.csv`, `sensitivity_ranges.csv` | 6,750 combinations of shock, retained reserve, reserve-field choice and independently shifted endpoints. |
| `matched_assumption_order.csv` | 1,350 original-window comparisons using matching assumptions. |
| `alternative_buffers.csv` | PRC, RTOLCAP and RTOLCAP plus RTOFFCAP at 15 GW. |
| `diagnostic_*.csv`, `diagnostic_windows.csv` | Six-hour maximum aggregation-gap illustrations. |
| `representative_series_*.csv`, `representative_periods.csv`, `hourly_gap_distribution.csv` | Median-positive-gap illustrations and the full hourly-gap distribution. |
| `execution_time_sensitivity.csv`, `exact_threshold_timing.csv` | Execution-time hold versus normalized-grid integration and the Uri threshold timestamp check. |
| `january_dedup.csv`, `summer_missing_slot.csv` | Actual duplicate-run alternatives and the missing July slot. |
| `toy_mixture_*`, `toy_class_means.json` | Illustrative clipped-normal mean REE, not empirical EUE. |
| `physical_boundary_examples.csv` | Analytically specified counterexamples, not fitted ERCOT resource models. |
| `table5_retained_anchor_sweep.csv`, `table6_chi_crossings.csv` | Retained-reserve sweep and integer-GW crossings. Labels are context, not a physical adequacy certification. |
| `tableS6_scarcity_consistency.csv` | Reserve-price internal coherence, using 500 hour-block bootstrap draws per comparison, seed 42. |
| `tableS7_envelope_shocks.csv` | Original-window outage-envelope magnitude anchors. |
| `tableS9_peak_fuel.csv`, `tableS10_tight_hour_context.csv` | Peak-hour fuel and tight-hour composition. |
| `incidence_depth.csv`, `uri_window_decomposition.csv` | Incidence/depth and energy shares inside stated operator-state windows. |
| `persistence_sensitivity.csv` | Retrospective forward-observation minimum, with explicit boundary rules. |
| `selection_check.csv` | Daily-minimum PRC ranking for 2022 that supports the Section 4 selection statements for the February and July windows (Supplementary Section S10). |
| `reserve_tail_summary.csv` | Median PRC and lower-tail durations (hours below the EEA1 trigger and below 3,000 MW, longest run below 3,000 MW) with chi at 5 and 15 GW, supporting the Section 5.6 July-versus-Uri comparison and Supplementary Table S27. |

## Persistence definition and checks

For positive horizon D, the nominal buffer at slot t is the nonnegative part of
`min(PRC[t:t+D]) - retained_reserve`, with the right endpoint excluded and all
D*12 five-minute samples retained. This is a future-observation minimum, not
independent evidence of resource activation, ramping, storage state of charge,
network deliverability or the ability to sustain an added shock.

`full_horizon` is the primary diagnostic: the extended record supplies all D
hours even when the look-ahead passes the central event end. Integration and
normalization still cover only the central event. `event_end_truncated` uses the
same rule except that the look-ahead is shortened at the event end. At D=0,
both rules are the original instantaneous screen. The grid covers five events,
two boundary rules, four horizons (0/1/2/4 hours), two shocks and two retained
reserves, yielding 160 rows.

For January, 15 GW and 3 GW retained, full-horizon chi rounds to 0.424, 0.460,
0.491 and 0.547 at D=0,1,2,4 hours. Truncating at the event end instead gives
0.424, 0.460, 0.490 and 0.546. Both rows are reported rather than silently using
a shrinking look-ahead. A pandas forward-window calculation is checked against
an independently implemented deque algorithm. Increasing D must not reduce
REE, and complete look-ahead must not give less REE than endpoint truncation.

## Verification boundary

All 39 reference outputs are regenerated, including the persistence diagnostic, the 2022 selection check and the reserve-tail summary.
This package reproduces scientific calculations and figure sources; bibliography
entries, quoted review comments and Word typesetting are not computational outputs.
Source-data extracts allow internal source-execution comparisons, not independent
authentication of upstream measurements.
