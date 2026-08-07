# Data provenance and copyright

This package ships **derived** operating-data panels only. It does **not** redistribute
raw ERCOT files. This document records the public ERCOT source products, the access date,
and the transformation applied to produce each derived panel, so that a user with the raw
downloads can independently reimplement the documented transformations.

## Source products (public ERCOT)

All raw inputs were downloaded from the Electric Reliability Council of Texas (ERCOT) on
**3 June 2026**. The products used are:

| product | ERCOT report | role |
| --- | --- | --- |
| Real-Time ORDC and Reliability Deployment Price Adders and Reserves by SCED Interval | RTM ORDC price-adder / reserves | five-minute PRC, RTOLCAP, RTOFFCAP, RTORDPA |
| Actual System Load by Weather Zone | NP6-345-CD | hourly system load |
| Native Load archive | hourly native load | hourly load cross-check |
| Hourly Resource Outage Capacity | NP3-233-CD | hourly outage-capacity snapshots |
| Interconnection Generation by Fuel | Fuel-mix workbook | quarter-hour fuel-category generation |

The raw products are subject to ERCOT's own terms of use and are available from ERCOT. The
event windows follow the official event reports for Winter Storm Uri (Feb 2021), Winter
Storm Elliott (Dec 2022), and the January 2025 Arctic Events.

## Why derived data are redistributed instead of raw

The ERCOT SCED disclosure record contains many operating fields (system lambda, batch
identifiers, and roughly thirty reserve-product columns) that the REE screen does not use.
Rather than republish those disclosure records, this package publishes only the analytical
quantities the method defines, produced as follows.

## Derivation of each panel

### `data/interval_reserve/{event}_interval_reserve.csv`
From the five-minute SCED reserve product:
1. parse the SCED timestamp and floor it to a five-minute slot;
2. keep only the analytical columns `PRC`, `RTOLCAP`, `RTOFFCAP`, `RTORDPA`;
3. within each slot, keep the latest SCED run (`drop_duplicates(keep="last")`);
4. restrict to the event window `[start, end)` given in `ree.config.EVENTS`.

Output columns: `slot, prc_mw, rtolcap_mw, rtoffcap_mw, rtordpa`.
Interval counts: Uri 3456, Elliott 2592, January 2025 1728 (five-minute intervals).

### `data/hourly_panels/{event}_hourly_panel.csv`
Hourly aggregation of the SCED reserve product joined to load and outage:
- PRC aggregated to hourly minimum and mean; RTORDPA to hourly maximum;
- load from Actual System Load by Weather Zone;
- outage capacity from the last Hourly Resource Outage Capacity snapshot at or before each
  hour end (resource, IRR, and total-envelope columns);
- Uri and Elliott panels also carry hourly fuel-category output.

### `data/fuel_panels/{event}_fuel_panel.csv`
From the Interconnection Generation by Fuel workbook (quarter-hour MWh):
1. select the event window;
2. keep FINAL settlement rows where present;
3. sum the four quarter-hour labels within each clock hour to hourly MWh (interpreted as
   average MW over the hour);
4. combine `Gas` and `Gas-CC` into a single `gas_mw` column.

Output columns: `datetime, wind_mw, solar_mw, gas_mw, coal_mw, nuclear_mw, fuel_total_mw`.

### `data/outage_panels/{event}_outage_snapshot.csv`
The Hourly Resource Outage Capacity snapshots assigned to each hour end (last report at or
before the hour end), retaining the resource, IRR, and total-envelope quantities.

## Rebuilding from raw

This repository ships the derived panels, not a raw-to-panel converter. The transformation
steps documented above are small and self-contained, and the analytical columns and window
definitions are all in `ree.config`, so they can be reimplemented against raw ERCOT downloads
placed in a local `data_raw/` directory. The published derived panels reproduce every
numerical table and all analysis figures via `python scripts/run_all.py`.

## License of the derived data

The derived panels in `data/` are released under CC BY 4.0. ERCOT retains all rights in the
underlying raw products.

## Sensitivity inputs (`data/sensitivity/`)

Two derived files support the January 2025 sensitivity tables:

- `january_2025_dedup_variants.csv` (Table S12): from the five-minute SCED reserve product,
  three PRC series are formed by resolving repeated SCED runs within a slot under the
  latest-run, first-run, and within-slot-mean rules. Only the PRC values are retained.
- `january_2025_outage_snapshot_variants.csv` (Table S11): from the Hourly Resource Outage
  Capacity product, the zonal resource / IRR / new-equipment columns are summed to system
  totals and assigned to each hour under two rules — the contemporaneous rule (last posting
  at or before the hour end) and the latest-overall rule (last posting for that hour end).
  Only the aggregated outage MW columns are retained.
