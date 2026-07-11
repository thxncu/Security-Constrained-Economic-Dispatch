# Data dictionary

All panels are **derived** transformations of public ERCOT products (see `PROVENANCE.md`).
Times are local ERCOT time. Energies and capacities are in MW unless stated; prices in USD/MWh.

## `data/interval_reserve/`

Five-minute reserve series (native REE input, Eq. 6).

**`elliott_2022_interval_reserve.csv`** (2592 rows)

| column | description |
| --- | --- |
| `slot` | Five-minute interval timestamp (floored SCED timestamp), local ERCOT time. |
| `prc_mw` | Physical Responsive Capability (PRC), MW: ERCOT system-level responsive reserve. |
| `rtolcap_mw` | Real-Time Online Reserve Capacity (RTOLCAP), MW. |
| `rtoffcap_mw` | Real-Time Offline Reserve Capacity (RTOFFCAP), MW. |
| `rtordpa` | Real-Time ORDC Reserve Demand-adder Price (RTORDPA), USD/MWh. |

**`january_2025_interval_reserve.csv`** (1728 rows)

| column | description |
| --- | --- |
| `slot` | Five-minute interval timestamp (floored SCED timestamp), local ERCOT time. |
| `prc_mw` | Physical Responsive Capability (PRC), MW: ERCOT system-level responsive reserve. |
| `rtolcap_mw` | Real-Time Online Reserve Capacity (RTOLCAP), MW. |
| `rtoffcap_mw` | Real-Time Offline Reserve Capacity (RTOFFCAP), MW. |
| `rtordpa` | Real-Time ORDC Reserve Demand-adder Price (RTORDPA), USD/MWh. |

**`uri_2021_interval_reserve.csv`** (3456 rows)

| column | description |
| --- | --- |
| `slot` | Five-minute interval timestamp (floored SCED timestamp), local ERCOT time. |
| `prc_mw` | Physical Responsive Capability (PRC), MW: ERCOT system-level responsive reserve. |
| `rtolcap_mw` | Real-Time Online Reserve Capacity (RTOLCAP), MW. |
| `rtoffcap_mw` | Real-Time Offline Reserve Capacity (RTOFFCAP), MW. |
| `rtordpa` | Real-Time ORDC Reserve Demand-adder Price (RTORDPA), USD/MWh. |

## `data/hourly_panels/`

Hourly merged panels (load, PRC aggregates, outage, and fuel where present).

**`elliott_2022_hourly_panel.csv`** (216 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `load_mw` | Hourly system load, MW. |
| `prc_min_mw` | Minimum PRC within the hour, MW. |
| `prc_mean_mw` | Mean PRC within the hour, MW. |
| `rtordpa_max` | Maximum RTORDPA within the hour, USD/MWh. |
| `rtolhsl_mean` | Mean Real-Time Online High Sustained Limit within the hour, MW. |
| `sced_intervals` | Number of SCED intervals observed in the hour. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_outage_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |
| `wind_mw` | Hourly wind output, MW. |
| `solar_mw` | Hourly solar output, MW. |
| `gas_mw` | Hourly gas output (Gas + Gas-CC), MW. |
| `coal_mw` | Hourly coal output, MW. |
| `nuclear_mw` | Hourly nuclear output, MW. |
| `fuel_total_mw` | Sum of the listed fuel categories, MW. |

**`january_2025_hourly_panel.csv`** (1416 rows)

| column | description |
| --- | --- |
| `hour_start` | Hour-start timestamp, local ERCOT time. |
| `n_sced` | Number of SCED intervals observed in the hour. |
| `prc_min` | Minimum PRC within the hour, MW. |
| `prc_mean` | Mean PRC within the hour, MW. |
| `prc_max` | Maximum PRC within the hour, MW. |
| `rtordpa_max` | Maximum RTORDPA within the hour, USD/MWh. |
| `rtordpa_mean` | Mean RTORDPA within the hour, USD/MWh. |
| `rtolhsl_min` | Minimum RTOLHSL within the hour, MW. |
| `rtolhsl_mean` | Mean Real-Time Online High Sustained Limit within the hour, MW. |
| `rtolhsl_max` | Maximum RTOLHSL within the hour, MW. |
| `rtolcap_min` | Minimum RTOLCAP within the hour, MW. |
| `rtolcap_mean` | Mean RTOLCAP within the hour, MW. |
| `rtbp_mean` | Mean real-time block price within the hour, USD/MWh. |
| `lambda_mean` | Mean system lambda within the hour, USD/MWh. |
| `load_total_weatherzone` | Hourly system load summed across weather zones, MW. |
| `load_total_native` | Hourly ERCOT native load, MW. |
| `resource_outage_mw` | Resource (dispatchable) outage capacity, MW. |
| `irr_outage_mw` | Intermittent renewable resource outage capacity, MW. |
| `new_equipment_mw` | New-equipment outage capacity, MW. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_envelope_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |
| `postedDatetime` | Timestamp the outage snapshot was posted. |

**`uri_2021_hourly_panel.csv`** (288 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `load_mw` | Hourly system load, MW. |
| `prc_min_mw` | Minimum PRC within the hour, MW. |
| `prc_mean_mw` | Mean PRC within the hour, MW. |
| `rtordpa_max` | Maximum RTORDPA within the hour, USD/MWh. |
| `rtolhsl_mean` | Mean Real-Time Online High Sustained Limit within the hour, MW. |
| `sced_intervals` | Number of SCED intervals observed in the hour. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_outage_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |
| `wind_mw` | Hourly wind output, MW. |
| `solar_mw` | Hourly solar output, MW. |
| `gas_mw` | Hourly gas output (Gas + Gas-CC), MW. |
| `coal_mw` | Hourly coal output, MW. |
| `nuclear_mw` | Hourly nuclear output, MW. |
| `fuel_total_mw` | Sum of the listed fuel categories, MW. |

## `data/fuel_panels/`

Hourly fuel-category output.

**`elliott_2022_fuel_panel.csv`** (216 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `Biomass` | See PROVENANCE.md. |
| `Coal` | See PROVENANCE.md. |
| `Gas` | See PROVENANCE.md. |
| `Gas-CC` | See PROVENANCE.md. |
| `Hydro` | See PROVENANCE.md. |
| `Nuclear` | See PROVENANCE.md. |
| `Other` | See PROVENANCE.md. |
| `Solar` | See PROVENANCE.md. |
| `WSL` | See PROVENANCE.md. |
| `Wind` | See PROVENANCE.md. |
| `gas_mw` | Hourly gas output (Gas + Gas-CC), MW. |
| `wind_mw` | Hourly wind output, MW. |
| `solar_mw` | Hourly solar output, MW. |
| `coal_mw` | Hourly coal output, MW. |
| `nuclear_mw` | Hourly nuclear output, MW. |
| `fuel_total_mw` | Sum of the listed fuel categories, MW. |

**`january_2025_fuel_panel.csv`** (144 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `wind_mw` | Hourly wind output, MW. |
| `solar_mw` | Hourly solar output, MW. |
| `gas_mw` | Hourly gas output (Gas + Gas-CC), MW. |
| `coal_mw` | Hourly coal output, MW. |
| `nuclear_mw` | Hourly nuclear output, MW. |
| `fuel_total_mw` | Sum of the listed fuel categories, MW. |

**`uri_2021_fuel_panel.csv`** (288 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `Biomass` | See PROVENANCE.md. |
| `Coal` | See PROVENANCE.md. |
| `Gas` | See PROVENANCE.md. |
| `Gas-CC` | See PROVENANCE.md. |
| `Hydro` | See PROVENANCE.md. |
| `Nuclear` | See PROVENANCE.md. |
| `Other` | See PROVENANCE.md. |
| `Solar` | See PROVENANCE.md. |
| `Wind` | See PROVENANCE.md. |
| `gas_mw` | Hourly gas output (Gas + Gas-CC), MW. |
| `wind_mw` | Hourly wind output, MW. |
| `solar_mw` | Hourly solar output, MW. |
| `coal_mw` | Hourly coal output, MW. |
| `nuclear_mw` | Hourly nuclear output, MW. |
| `fuel_total_mw` | Sum of the listed fuel categories, MW. |

## `data/outage_panels/`

Hourly outage-capacity snapshots.

**`elliott_2022_outage_snapshot.csv`** (216 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `TotalResourceMW` | Total resource outage capacity in the snapshot, MW. |
| `TotalIRRMW` | Total IRR outage capacity in the snapshot, MW. |
| `TotalNewEquipResourceMW` | Total new-equipment resource outage capacity, MW. |
| `post_datetime` | Snapshot posting timestamp. |
| `hour_end` | Hour-end timestamp the snapshot is assigned to. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_outage_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |

**`january_2025_outage_snapshot.csv`** (503 rows)

| column | description |
| --- | --- |
| `hour_start` | Hour-start timestamp, local ERCOT time. |
| `resource_outage_mw` | Resource (dispatchable) outage capacity, MW. |
| `irr_outage_mw` | Intermittent renewable resource outage capacity, MW. |
| `new_equipment_mw` | New-equipment outage capacity, MW. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_envelope_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |
| `postedDatetime` | Timestamp the outage snapshot was posted. |

**`uri_2021_outage_snapshot.csv`** (288 rows)

| column | description |
| --- | --- |
| `datetime` | Hour-start timestamp, local ERCOT time. |
| `TotalResourceMW` | Total resource outage capacity in the snapshot, MW. |
| `TotalIRRMW` | Total IRR outage capacity in the snapshot, MW. |
| `TotalNewEquipResourceMW` | Total new-equipment resource outage capacity, MW. |
| `post_datetime` | Snapshot posting timestamp. |
| `hour_end` | Hour-end timestamp the snapshot is assigned to. |
| `res_irr_outage_mw` | Resource-plus-intermittent-renewable-resource outage capacity, MW (last snapshot at/before hour end). |
| `all_outage_mw` | Total outage capacity envelope, MW (last snapshot at/before hour end). |

## `data/sensitivity/`

Derived inputs for the January 2025 sensitivity tables. These isolate the small set of
extra quantities the sensitivity analyses need (multiple de-duplication rules and outage
snapshot rules) that are not required elsewhere.

**`january_2025_dedup_variants.csv`** (1728 rows) — supports Supplementary Table S12

| column | description |
| --- | --- |
| `slot` | Five-minute interval timestamp, local ERCOT time. |
| `prc_latest` | PRC under the latest-SCED-run de-duplication rule (central), MW. |
| `prc_first` | PRC under the first-SCED-run rule, MW. |
| `prc_mean` | PRC under the within-slot-mean rule, MW. |

**`january_2025_outage_snapshot_variants.csv`** — supports Supplementary Table S11

| column | description |
| --- | --- |
| `hour_start` | Hour-start timestamp, local ERCOT time. |
| `hour_end` | Hour-end timestamp, local ERCOT time. |
| `res_irr_mw` | Resource-plus-IRR outage capacity for that hour under the given rule, MW. |
| `all_env_mw` | Total outage-capacity envelope for that hour under the given rule, MW. |
| `rule` | Snapshot rule: `contemporaneous` (last posting at or before hour end) or `latest_overall`. |
