import numpy as np
import pytest
import systemictau as st

def test_compute_taus_shape():
    """Test that compute_taus returns the correct shapes."""
    np.random.seed(42)
    X = np.random.randn(100, 3)
    taus_global, taus_per_module = st.compute_taus(X, window_size=13)
    
    assert len(taus_global) == 100
    assert taus_per_module.shape == (100, 3) # If modules not specified, it computes pairwise against the system

def test_accumulate_time():
    """Test that accumulate_time produces monotonically non-decreasing T."""
    np.random.seed(42)
    # Simulate a tau signal that dips below and above the chaotic threshold (0.41)
    taus = np.sin(np.linspace(0, 4*np.pi, 200)) 
    
    T, dtk, gate, depths = st.accumulate_time(taus)
    
    assert len(T) == 200
    # T must be non-decreasing
    assert np.all(np.diff(T) >= 0)
    
def test_hyper_persistence_logic():
    """Test that hyper_persistence identifies stable windows correctly."""
    np.random.seed(42)
    # Taus fluctuating but strictly above 0.41
    taus = np.random.uniform(0.42, 0.9, size=50)
    hp_z, core = st.hyper_persistence(taus)
    
    assert len(hp_z) == 50
    assert len(core) == 50
    # Just verify that hp_z is an array of floats
    assert hp_z.dtype == float
