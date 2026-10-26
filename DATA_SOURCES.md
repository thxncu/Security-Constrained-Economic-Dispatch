# Data sources and transformation rules

## Source products

The analysis uses historical ERCOT reserve/price-adder records (PRC, RTOLCAP,
RTOFFCAP and RTORDPA), Actual System Load by Weather Zone / Native Load data,
Interval Generation by Fuel workbooks, and Hourly Resource Outage Capacity
records. The study's recorded original data-access date is June 3, 2026.
This package redistributes derived analytical fields, not the original operator
workbooks or download ZIPs. Raw source authenticity and measurement accuracy are
outside the executable comparisons in this distribution.

Recorded source filenames include:

* `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_2021.xlsx` (February 2021 records).
* `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_2023.xlsx` (the selected workbook's actual
  record timestamps cover 2022, despite the filename).
* `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_2025_Jan_Feb(1).csv`.
* `Native_Load_2021.zip`, `Native_Load_2022.zip`, and
  `act_sys_load_by_wzn(2).csv`.
* `IntGenbyFuel2021.xlsx`, `IntGenbyFuel2022.xlsx`, and
  `IntGenbyFuel2025 (1)(2).xlsx`.
* Historical event outage-capacity CSVs and
  `00013103.np3-233-cd.hourly_res_outage_cap.20260603.050210_csv.zip`.

The source transformations below describe the preserved data. The default run
reconstructs reserve panels from the included execution extracts. It does not
rerun the original hourly-workbook extraction or fetch missing raw archives.

## Windows and timestamps

`data/events.json` defines start-inclusive, end-exclusive ERCOT local-time
windows. Uri covers February 10 to February 22, 2021 (288 hours); Elliott covers
December 20 to December 29, 2022 (216 hours); January covers January 19 to
January 25, 2025 (144 hours). The additional February 2 to February 7 and July 10
to July 15, 2022 windows each contain 120 hours. There is no daylight-saving
clock change inside these windows or their one-day margins. The verification
script rejects an unexpected repeated-clock flag instead of silently combining
ambiguous local times.

## Included schemas

`*_selected_runs.csv` contains actual execution timestamps (`stamp`), batch IDs,
repeated-hour flags and four analytical fields. It includes one day on either
side of the central window. `slot` is the timestamp floored to five minutes and
is not the original observation time. There are 13,863 extracted executions
across the five extended records.

`*_reserve.csv` contains the central five-minute grid; `*_reserve_extended.csv`
adds one day on each side. Each has `slot`, `prc_mw`, `rtolcap_mw`,
`rtoffcap_mw`, `rtordpa` and `imputed`. Reserve fields are MW and RTORDPA is
USD/MWh. The latest execution, with stable timestamp/batch ordering, is retained
in each five-minute slot.

Only the July 12, 2022 17:40 slot is missing. The central normalized grid
interpolates the immediately adjacent values, flags that slot, and reports
alternative treatment and residual bounds separately. PRC at that imputed slot
is 4,033.725 MW. No imputed value is presented as an observed execution.

`*_hourly.csv` has an hour-start `datetime`, hourly load, wind and solar, with
additional fuel and outage context where available. Four consecutive 15-minute
energy entries are summed to hourly MWh, numerically equal to average MW for a
one-hour interval. The source workbook's final `0:00` column completes the
preceding 23:00 to 24:00 hour and is included. Gas combines Gas and Gas-CC.
Reported small nonzero solar values and signed generation categories are retained.
The settlement-based fuel series supports retrospective profiles, not real-time
forecasts. Resource/IRR outage fields for the three original windows use the
latest report posted no later than the relevant hour end. No contemporaneous
outage series is invented for the two additional seasonal windows.

`prc_daily_2022.csv` has one row for each 2022 operating day: the number of
observed five-minute slots, the daily minimum PRC in MW, the slot of that
minimum, its repeated-hour flag, and the number of slots below 3,500 MW. It is
derived from the same 2022 reserve workbook with the same latest-execution
rule as the event panels. Slots in the repeated hour of November 6, 2022 are
kept separately by their repeated-hour flag, so that day has 300 slots and
March 13 has 276. Days with a missing execution slot keep their observed count.
The file supports the case-selection statements only; it is not used in any
REE calculation.

## Reconstruction and numerical checks

`verify_panels.py` rebuilds the central and extended reserve grids from the
included execution extracts and compares all analytical fields and imputation
flags. `selection_check.py` confirms that the 2022 daily-minimum file agrees
exactly with those panels on every overlapping day. `independent_numeric_audit.py` uses a separate calculation path for fixed,
wind-shaped and assumption-grid results. These checks establish internal data and
arithmetic consistency. They do not establish physical feasibility, event
representativeness, independent raw-source authentication or an REE-to-EUE map.
