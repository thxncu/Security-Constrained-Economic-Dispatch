"""ree: SCED-native reserve-exceedance energy screening for public-data reliability analysis.

Public API mirrors the manuscript structure:

    io           load derived event panels (Section 4)
    estimator    native/hourly-minimum REE and chi (Section 3)
    shocks       three shock-trajectory families (Section 3.3)
    consistency  reserve-scarcity coherence checks (Section 6.3 / S4)
    montecarlo   illustrative Eq. (3) bridge to EUE (Section 6.1)
    config       constants, event metadata, thresholds
"""
from . import config, io, estimator, shocks, consistency, montecarlo

__all__ = ["config", "io", "estimator", "shocks", "consistency", "montecarlo"]
__version__ = "1.0.0"
