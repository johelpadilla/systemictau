__version__ = "3.0.0-dev"
from .core import compute_taus, systemic_tau, SystemicTauResult
from .recd import compute_recd_increments, accumulate_time, gate_function
from .layers import (
    hyper_persistence,
    rolling_rqa,
    critical_mass_metric,
    compute_antisynchronization,
    extract_joint_episodes,
    detect_reorganization_frob,
    detect_reorganization_ks,
    consensus_transition
)
from .fractal import estimate_higuchi_dimension
from .generators import ChaosGenerator
from .visualization import plot_tau_evolution, plot_joint_episodes, plot_ontological_layers
from .data import preprocess, from_dataframe, from_xarray
from .validation import evaluate_early_warning
from .gis import spatial_tau

__all__ = [
    "systemic_tau",
    "SystemicTauResult",
    "compute_taus",
    "compute_recd_increments",
    "accumulate_time",
    "gate_function",
    "hyper_persistence",
    "rolling_rqa",
    "critical_mass_metric",
    "compute_antisynchronization",
    "extract_joint_episodes",
    "detect_reorganization_frob",
    "detect_reorganization_ks",
    "consensus_transition",
    "estimate_higuchi_dimension",
    "ChaosGenerator",
    "plot_tau_evolution",
    "plot_joint_episodes",
    "plot_ontological_layers",
    "preprocess",
    "from_dataframe",
    "from_xarray",
    "evaluate_early_warning",
    "spatial_tau"
]
