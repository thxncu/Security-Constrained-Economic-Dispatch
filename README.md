# SCED-native reserve-exceedance energy (REE) screening

Replication package for:

> **Security-Constrained Economic Dispatch (SCED)-native reserve-exceedance estimation for public-data reliability screening in power systems.**
> Submitted to *Electric Power Systems Research* (Ms. Ref. EPSR-D-26-05120).

This repository reproduces every numerical table and the data series behind every figure in the manuscript from **derived,
copyright-safe** operating-data panels for three ERCOT winter stress events. It does
**not** redistribute raw ERCOT files; see [Data and copyright](#data-and-copyright).

---

## What this package computes

The reserve-exceedance energy (REE) screen maps a counterfactual resource shock onto an
observed operating-reserve trajectory and reports the conditional attenuation factor χ,
the fraction of the shock that is not absorbed by the operating buffer. The method is a
transparent, auditable first screen that decides when a full chronological adequacy model
is worth commissioning; it is deliberately kept distinct from expected unserved energy
(EUE), which requires probabilities over adequacy states.

The package reproduces, among other results:

- native REE and χ for a 15 GW shock: **0.239 / 0.492 / 0.712** (January 2025 / Elliott / Uri) at full buffer, rising to **0.424 / 0.692 / 0.899** with 3 GW retained;
- the hourly-minimum overstatement of **1.2 % to 37.6 %** relative to native integration;
- the shock-magnitude sweep and χ-crossing thresholds;
- event-specific outage-envelope and time-varying wind-derating shocks;
- alternative operating-buffer definitions;
- documented operating-state alignment and the Uri window decomposition;
- the tight-hour incidence/depth mechanism decomposition;
- the illustrative Monte Carlo bridge to EUE (**577 GWh per winter**, demonstration values).

Second-revision additions (round-2 referee requests):

- day-block bootstrap 95 % intervals for the conditional REE and χ estimates
  (`tableS13_block_bootstrap_ci.csv`); at 15 GW the χ intervals of adjacent events do
  not overlap under either retained-reserve case, so the severity ordering is robust
  to within-event day composition;
- a numerical verification that REE is convex in the shock magnitude
  (`tableS14_convexity_check.csv`), supporting the convexity proposition in the paper;
- the mixture decomposition of the Monte Carlo bridge, EUE = Σ p_c · E[REE | c], with
  class-conditional means and EUE reweighted under alternative winter-event-class
  probability vectors (`tableS15_mc_prob_sensitivity.csv`), so readers can substitute
  their own class probabilities without re-running the simulation;
- a runtime and environment report (`runtime_report.csv`): the full pipeline
  regenerates every output in roughly ten seconds on a commodity machine.

---

## Quick start

```bash
# 1. create the environment
pip install -r requirements.txt          # or: conda env create -f environment.yml

# 2. regenerate every numerical table and all analysis figures
python scripts/run_all.py

# 3. confirm the outputs match the manuscript
python scripts/verify_against_manuscript.py
```

`run_all.py` writes CSV tables to `results/` and PNG figures to `figures/`.
`verify_against_manuscript.py` asserts that the regenerated numbers match the values
reported in the paper and exits non-zero on any mismatch.

Every numerical table in the paper is regenerated: main-text Tables 3-8 and Supplementary Tables S2, S3, S5-S16, plus the runtime and environment report. Analysis figures (Figures 2-3 and S1-S6) are regenerated from the same panels up to the final styling applied in the article file; the workflow diagram (Figure 1) is illustrative and prepared in the article file. The four
purely descriptive items (Table 1 and Table S1 nomenclature, Table 2 qualitative
comparison, Table S4 evidence-hierarchy tiers) contain no computed values and are not
emitted.

Each numbered script under `scripts/` is standalone and documents which manuscript
table or figure it produces, so individual results can be regenerated in isolation.

---

## Repository layout

```
.
├── README.md                     this file
├── LICENSE                       MIT (code) + CC BY 4.0 note (derived data)
├── CITATION.cff                  how to cite this package
├── requirements.txt              pip dependencies
├── environment.yml               conda environment
├── data/
│   ├── DATA_DICTIONARY.md        column-by-column description of every panel
│   ├── PROVENANCE.md             how the derived panels were produced from ERCOT
│   ├── interval_reserve/         five-minute reserve series per event (native REE input)
│   ├── hourly_panels/            hourly load / PRC / outage panels
│   ├── fuel_panels/              hourly fuel-category output
│   ├── outage_panels/            hourly outage-capacity snapshots
│   └── sensitivity/              derived inputs for the January sensitivity tables (S11, S12)
├── src/ree/                      installable analysis library
│   ├── config.py                 constants, event metadata, thresholds, seeds
│   ├── io.py                     loaders for the derived panels
│   ├── estimator.py              native / hourly-minimum REE and χ (Eqs. 1-6)
│   ├── shocks.py                 three shock-trajectory families (Section 3.3)
│   ├── consistency.py            reserve-scarcity coherence checks (Section 6.3 / S4)
│   ├── montecarlo.py             illustrative Eq. (3) bridge to EUE (Section 6.1)
│   └── bootstrap.py              day-block bootstrap intervals and convexity check (R2 additions)
├── scripts/                      one script per manuscript table/figure group
│   ├── 01_reserve_exceedance_tables.py     (Tables 4, 5; overstatement)
│   ├── 02_shock_sweep_and_crossings.py     (Table 6, Figure 2)
│   ├── 03_event_specific_and_wind_shocks.py (Table 7, Table S7)
│   ├── 04_alternative_buffers.py           (Table S8)
│   ├── 05_documented_state_alignment.py    (Table 8, Figure 3; Uri decomposition)
│   ├── 06_mechanism_decomposition.py       (Tables S9, S10; incidence/depth)
│   ├── 07_montecarlo_bridge.py             (MC bridge, Figure S6, Table S15)
│   ├── 08_consistency_checks.py            (Table S6)
│   ├── 09_event_summary_audit.py           (Table 3, Table S3)
│   ├── 10_supplementary_tables.py          (Tables S2, S5, S11, S12)
│   ├── 11_supplementary_figures.py         (Figures S1-S5)
│   ├── 12_workflow_figure.py               (Figure 1)
│   ├── 13_bootstrap_ci.py                  (Tables S13, S14; R2 additions)
│   ├── run_all.py                          (regenerate everything; writes runtime_report.csv)
│   └── verify_against_manuscript.py        (assert outputs match the paper)
├── results/                      regenerated CSV tables (tracked for convenience)
└── figures/                      regenerated PNG figures
```

---

## Data and copyright

The analysis uses public ERCOT data products, but this repository **does not redistribute
raw ERCOT files**. Instead it ships **derived panels** that are transformations of those
products:

- `data/interval_reserve/` contains only the five analytical columns the method defines
  (timestamp, PRC, RTOLCAP, RTOFFCAP, RTORDPA), stripped from the full ERCOT SCED
  disclosure record;
- `data/hourly_panels/`, `data/fuel_panels/`, and `data/outage_panels/` contain hourly
  aggregations and computed quantities.

The exact source products, access date, and the transformation applied to each are
documented in [`data/PROVENANCE.md`](data/PROVENANCE.md). To rebuild the panels from the
raw ERCOT downloads yourself, follow the steps there. The original raw products are
available from ERCOT and are subject to ERCOT's own terms of use.

---

## Reproducibility notes

- All randomness is seeded (`ree.config.MC_SEED = 2026`, `ree.config.CONSISTENCY_SEED = 42`);
  the Monte Carlo bridge and the bootstrap confidence intervals are deterministic.
- Native REE integrates over five-minute intervals (`INTERVAL_HOURS = 5/60`); the
  hourly-minimum screen is provided for comparison only.
- Results were generated with the pinned versions in `requirements.txt`.

## License and citation

Code is released under the MIT License. Derived data are released under CC BY 4.0. See
[`LICENSE`](LICENSE) and [`CITATION.cff`](CITATION.cff).
