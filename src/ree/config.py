"""Configuration constants for the REE screening replication package.

All values here are documented in the manuscript (Sections 3-6) and are kept in one
place so that scripts and the library share a single source of truth.
"""
from __future__ import annotations
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths (resolved relative to the package root, i.e. the repository directory).
# ----------------------------------------------------------------------------
PKG_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PKG_ROOT / "data"
INTERVAL_DIR = DATA_DIR / "interval_reserve"
HOURLY_DIR = DATA_DIR / "hourly_panels"
FUEL_DIR = DATA_DIR / "fuel_panels"
OUTAGE_DIR = DATA_DIR / "outage_panels"
RESULTS_DIR = PKG_ROOT / "results"
FIGURES_DIR = PKG_ROOT / "figures"
SENSITIVITY_DIR = DATA_DIR / "sensitivity"

# ----------------------------------------------------------------------------
# Native SCED dispatch interval length (Section 3.1). ERCOT SCED runs nominally
# every five minutes, so each native interval contributes 5/60 hours of energy.
# ----------------------------------------------------------------------------
INTERVAL_HOURS = 5.0 / 60.0

# ----------------------------------------------------------------------------
# Event panels (Section 4). Keys are the file stems used throughout the package.
# `window` is [start, end) in local interval time; `label` is the manuscript name.
# `expected_intervals` is the exact five-minute interval count used in the audit.
# ----------------------------------------------------------------------------
EVENTS = {
    "uri_2021": {
        "label": "Winter Storm Uri 2021",
        "short": "Uri 2021",
        "window": ("2021-02-10 00:00", "2021-02-22 00:00"),
        "hours": 288,
        "expected_intervals": 3456,
        # EEA1 reserve trigger in force at the event (MW). Uri used the pre-Nov-2021
        # 2,300 MW EEA1 trigger (Section 5.3, Table 8).
        "eea1_trigger_mw": 2300,
    },
    "elliott_2022": {
        "label": "Winter Storm Elliott 2022",
        "short": "Elliott 2022",
        "window": ("2022-12-20 00:00", "2022-12-29 00:00"),
        "hours": 216,
        "expected_intervals": 2592,
        "eea1_trigger_mw": 2300,
    },
    "january_2025": {
        "label": "January 2025 main",
        "short": "Jan. 2025",
        "window": ("2025-01-19 00:00", "2025-01-25 00:00"),
        "hours": 144,
        "expected_intervals": 1728,
        # January 2025 used the post-Nov-2023 2,500 MW EEA1 trigger (Section 5.3).
        "eea1_trigger_mw": 2500,
    },
}
EVENT_ORDER = ["january_2025", "elliott_2022", "uri_2021"]  # ascending severity

# ----------------------------------------------------------------------------
# Screening parameters.
# ----------------------------------------------------------------------------
# Central fixed shocks (Section 3.3, Table 4).
FIXED_SHOCKS_GW = [10, 15]
# Central retained-reserve cases (Section 3.2).
CENTRAL_RETAINED_GW = [0, 3]
# Shock-magnitude sweep (Section 5.2, Figure 2, Table 6).
SWEEP_SHOCKS_GW = list(range(1, 26))
# chi thresholds for the crossing table (Section 5.2, Table 6) and escalation
# heuristic (Section 6.3).
CHI_THRESHOLDS = [0.05, 0.10, 0.25, 0.50]
ESCALATION_CHI = 0.10
# Retained-reserve anchor sweep for the 15 GW shock (Section 5.1, Table 5).
# (retained_MW, label) pairs anchored to ERCOT operating thresholds.
RETAINED_ANCHORS = [
    (0, "Full PRC buffer"),
    (1375, "EEA3 trigger in force at Uri (pre-Nov. 2021)"),
    (1430, "EEA3 trigger in force at Elliott"),
    (1500, "EEA3 trigger since Nov. 2023"),
    (1750, "EEA2 trigger through 2023"),
    (2000, "EEA2 trigger since Nov. 2023"),
    (2300, "EEA1 trigger through 2023; pre-2019 ORDC minimum contingency level"),
    (2500, "EEA1 trigger since Nov. 2023"),
    (3000, "ERCOT low-reserve analysis boundary; central retained case"),
    (5000, "Stringent screening case"),
]
# Wind-derating fractions for the time-varying shock family (Section 5.2, Table 7).
WIND_ALPHAS = [0.5, 1.0]
# Tight-hour threshold for the mechanism decomposition (Section 5.3): minimum PRC
# below 8 GW.
TIGHT_PRC_MW = 8000

# ----------------------------------------------------------------------------
# Monte Carlo bridge (Section 6.1). All probabilities are illustrative
# demonstration values, not empirical frequencies.
# ----------------------------------------------------------------------------
MC_SEED = 2026
MC_DRAWS = 20000
# Winter-event class demonstration probabilities: none / Jan / Elliott / Uri.
MC_CLASS_PROBS = {"none": 8 / 15, "january_2025": 4 / 15, "elliott_2022": 2 / 15, "uri_2021": 1 / 15}
# Truncated-normal shock (MW): mean, sd, lower, upper.
MC_SHOCK = {"mean": 12000, "sd": 4000, "lo": 2000, "hi": 25000}

# Bootstrap seed for the reserve-scarcity consistency check (Section 6.3 / S4).
CONSISTENCY_SEED = 42
CONSISTENCY_BOOTSTRAP = 500

# ----------------------------------------------------------------------------
# Report-level severity anchors (Supplementary Table S5). The reported
# unavailable-generation and firm-load-shed figures are external constants taken
# from the cited FERC/NERC event reports [14-16]; they are severity context only
# and are not used as hourly model targets. Max outage-envelope columns are
# recomputed from the panels by the script.
# ----------------------------------------------------------------------------
REPORT_ANCHORS = {
    # event: (reported_unavailable_generation_MW, firm_load_shed_MW, interpretation)
    "uri_2021": (61305, 23418, "Realized emergency event"),
    "elliott_2022": (90500, 5400, "Broader multi-region cold event"),
    "january_2025": (71022, 0, "Non-load-shed stress event"),
}

# ----------------------------------------------------------------------------
# Data-layer listing (Supplementary Table S2). Static description of the public
# ERCOT products and their role, emitted as a CSV so the package reproduces every
# table. See data/PROVENANCE.md for source products and access date.
# ----------------------------------------------------------------------------
DATA_LAYERS = [
    ("Load", "Actual System Load by Weather Zone; Native Load archive",
     "Hourly load and peak-time cross-check", "Uri, Elliott, January 2025"),
    ("Reserve and price adder",
     "Real-Time ORDC/Reliability Deployment Price Adders and Reserves by SCED Interval",
     "SCED PRC, RTORDPA, Real-Time Online Capacity, and Real-Time Online High Sustained Limit",
     "Uri, Elliott, January 2025"),
    ("Outage capacity", "Hourly Resource Outage Capacity",
     "Resource, intermittent renewable resource, and new-equipment outage envelopes",
     "Uri, Elliott, January 2025"),
    ("Fuel generation", "Interconnection Generation by Fuel",
     "15-minute fuel output aggregated to hourly profiles", "Uri, Elliott, January 2025"),
    ("FERC/NERC event reports", "FERC/NERC event and performance reports",
     "Report-level unavailable generation and firm-load-shed context", "Uri, Elliott, January 2025"),
]

# January 2025 windows for the outage-snapshot sensitivity (Supplementary Table S11).
JAN_SNAPSHOT_WINDOWS = {
    "Jan. 15-27 wide": ("2025-01-15 00:00", "2025-01-28 00:00"),
    "Jan. 19-24 main": ("2025-01-19 00:00", "2025-01-25 00:00"),
    "Jan. 21-22 peak-cold": ("2025-01-21 00:00", "2025-01-23 00:00"),
}
