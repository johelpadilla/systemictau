import numpy as np
import pytest
from systemictau import (
    systemic_tau,
    SystemicTauResult,
    ChaosGenerator
)

def test_systemic_tau_dataclass():
    """Test the unified systemic_tau function and SystemicTauResult dataclass."""
    np.random.seed(42)
    X = np.random.randn(100, 3)
    
    res = systemic_tau(X, window_size=13)
    
    # Check type
    assert isinstance(res, SystemicTauResult)
    
    # Check lengths
    assert len(res.taus_global) == 100
    assert res.taus_per_module.shape == (100, 3)
    
    # Check metadata
    assert res.metadata['window_size'] == 13
    assert res.metadata['n_components'] == 3
    assert res.metadata['method'] == 'kendall'

def test_chaos_generators():
    """Test the ChaosGenerator synthetic datasets."""
    n_steps = 100
    
    # Logistic map
    X_log = ChaosGenerator.logistic_map_coupled(n_steps, 3, coupling=0.1)
    assert X_log.shape == (100, 3)
    assert np.all(X_log >= 0) and np.all(X_log <= 1)
    
    # Lorenz
    X_lor = ChaosGenerator.lorenz_coupled(n_steps)
    assert X_lor.shape == (100, 3)
    
    # Rossler
    X_ros = ChaosGenerator.rossler_coupled(n_steps)
    assert X_ros.shape == (100, 3)
