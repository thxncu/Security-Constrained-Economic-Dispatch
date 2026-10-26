# Reproduction package

This archive supports the article "Security-Constrained Economic Dispatch (SCED)-native
reserve-exceedance estimation for public-data reliability screening in power systems:
evidence from five ERCOT operating windows". The version-specific DOI is shown on the
Zenodo record and in the article's Data and code availability statement; the GitHub
repository hosts the development copy. `CITATION.cff` and `.zenodo.json` carry the
citation metadata.

This package contains the analysis code, derived input panels and numerical
reference results for the five-window ERCOT reserve-exceedance study. Manuscript
files are not included or required.

## Run

Use Python 3.13.5 and the recorded package versions in `requirements.txt` in a
separate virtual environment. After installing these dependencies, the complete
analysis runs without network access or a raw-data archive.

```bash
python -m pip install -r requirements.txt
python verify_release.py
python run_all.py
```

Run these commands from the directory containing this README. Python must not be
invoked with `-O`, because the numerical scripts contain scientific assertions.
An existing output directory is never overwritten. To perform another run:

```bash
python run_all.py --output fresh_run_2
```

`fresh_run/work/results/` contains the regenerated full-precision tables and
verification reports. `fresh_run/work/figures/` contains regenerated PNG/SVG
figures. The top-level `fresh_run/run_report.json` must say `"status": "PASS"`.
`fresh_run/reference_comparison.json` gives each numerical comparison.

The runner begins with an empty result directory. It copies input data and code,
not reference results, into the isolated workspace. Only after the calculations
finish does it compare regenerated results with `reference/`. It also verifies
that input and package checksums are unchanged.

## Reporting checks

`code/reporting_checks.py` runs after the reserve-tail summary and asserts the
values quoted in the article for the following outputs:

- `matched_pair_comparison.csv` and `matched_pair_crossings.csv`: for all ten event
  pairs, the 1,350 matched combinations of shock, retained reserve, buffer and
  endpoint shifts in which the lower-listed event has smaller, equal or larger chi.
  The weak January <= Elliott <= Uri ordering holds in all 1,350 (153 ties, all with
  chi = 0 at 1-5 GW); July stays below Uri everywhere; February exceeds Elliott in 55
  PRC combinations with the end date shifted by +24 h.
- `buffer_headroom.csv` and `factor_widths_15gw.csv`: RTOLCAP versus PRC headroom in
  every slot, and one-factor chi widths at 15 GW including PRC versus RTOLCAP alone and
  the 0-4 h persistence increase.
- `persistence_vs_buffer_width.csv`: for the 20 primary event/shock/retention cases,
  the 0-4 h persistence increase against the PRC-versus-RTOLCAP and three-buffer widths
  at the same shock and retained reserve. Persistence is smaller in 19 cases; the
  exception is January 2025 at 10 GW without retained reserve, where chi is 0.043.
- `reporting_summary.csv`: chi, incidence, mean depth and observed lower-tail duration
  for all five windows (main Table 13). For a constant shock, chi equals the incidence
  fraction times mean depth divided by the shock, and the script asserts this identity.
- `native_hourly_periods.csv`: diagnostic (largest-gap) and typical
  (median-positive-gap) six-hour periods with the full-event overstatement.

The median-positive-gap outputs `typical_periods.csv` and `typical_period_series_*.csv`
are typical-period comparisons, whereas the `diagnostic_*.csv` periods are selected
largest-gap examples and are not representative operating periods.

## Scientific scope

The fixed-shock, wind-shock, event-endpoint, alternative-buffer, day-composition,
execution-time and illustrative mean-REE calculations reproduce the five-event
results. All 46 numerical reference files are independently regenerated before comparison.
Ancillary tables run directly from the included panels.

`persistence_sensitivity.csv` adds the explicitly specified forward-observation
minimum diagnostic for 0, 1, 2 and 4 hours, both with complete look-ahead support
and with an event-end-truncated window. Its 160 cases are independently checked
using two forward-minimum algorithms. See `REPRODUCTION_MAP.md` for definitions.
This result is a retrospective sensitivity, not an operational forecast or a
resource-energy constraint model.

`selection_check.csv` checks the case-selection statements for the additional 2022
windows against `data/prc_daily_2022.csv`, the daily minimum PRC for every 2022
operating day. The daily file must agree exactly with the observed slots of the
February, July and December 2022 event panels on all 25 overlapping days.

`reserve_tail_summary.csv` reports each central PRC path's median, minimum,
hours below the EEA1 trigger in force and below 3,000 MW, the longest run below
3,000 MW, and chi at 5 GW (no retained reserve) and 15 GW (3 GW retained). Its
chi values must match `sensitivity_surface.csv`.

PRC and the alternative buffers are nominal capability measures. REE is not
physical unserved energy, and the illustrative probability-weighted result is
not an empirical EUE estimate. Source-execution agreement is checked against
the included extracts; the upstream operator archive is not independently
re-downloaded or authenticated by this package.

This code-only distribution does not validate bibliographic claims, manuscript
wording or equation rendering in Word. The persistence table should be cited only
with the reported boundary rule.

## Contents

- `data/`: event definitions, hourly profiles, normalized reserve panels and
  timestamped execution extracts, with one-day reserve margins.
- `code/`: calculations, independent checks and figure-generation scripts.
- `reference/`: 46 numerical reference files, not copied into a fresh run.
- `DATA_SOURCES.md`: provenance, units, transformation and coverage rules.
- `REPRODUCTION_MAP.md`: output-to-analysis mapping and interpretation limits.
- `requirements.txt`, `LICENSE.txt`, `VERSION`, `SHA256SUMS.txt`: environment,
  licensing, distribution identification and integrity information.

Runtime depends on the machine. Exact runtime, dependency versions, result
comparisons and test counts are written by each execution. Figures are generated
rather than duplicated in the archive. Rendering may vary with local fonts;
numerical comparisons use an absolute tolerance of 1e-9 and relative tolerance
of 1e-12, with separate stricter checks for specified identities.

## Publication figures and grayscale printing

Publication layouts follow the article: Figure 2 and Figure 6 have two retention
panels, Figure 4 combines three native/hourly examples, Figure 5 combines three
nested-band panels, and Figure 7 uses only full-lookahead persistence results.
The original article colors are retained with redundant markers, line types and
hatches. No information depends on color alone. `code/publication_figures.py`
creates panels separately and composes their PNG and SVG files. Grayscale previews
are generated for visual checking. `FIGURE_MAP.md` identifies article images.

The publication checker verifies the actual curve arrays and the nested 9-, 18-
and 54-case sets. Automated contrast checks cannot replace visual inspection at
the final printed size. The retained full-precision numerical references are
unchanged by styling. Components are generated outputs, not required inputs.

The primary persistence analysis has 80 full-horizon cases. The same CSV includes
80 explicitly labeled event-end-truncated boundary checks. Only `full_horizon`
rows support main Table 12, Figure 7 and Supplementary Table S26.

The illustrative shock sampler is
`np.clip(rng.normal(12000, 4000), 2000, 25000)` in MW. The source-AST check tests
these four parameters. This is a clipped normal with endpoint masses, not a
conditional truncated distribution. No 31 GW upper limit is used.
