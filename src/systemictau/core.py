import numpy as np
import scipy.stats as stats
import itertools
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple
import time

def _kendall_tau_fast(x, y):
    """
    Computes Kendall's tau between two 1D arrays of ranks.
    Uses scipy.stats.kendalltau.
    """
    tau, _ = stats.kendalltau(x, y)
    return tau if not np.isnan(tau) else 0.0

def compute_taus(X, window_size=13):
    """
    Computes the Systemic Tau (global ordinal agreement) and per-module tau
    over a sliding window of a multivariate time series.
    
    Parameters:
    -----------
    X : numpy.ndarray
        Multivariate time series of shape (T, N) where T is time steps and N is the number of components.
    window_size : int, optional
        Size of the sliding window (default 13).
        
    Returns:
    --------
    taus_global : numpy.ndarray
        1D array of shape (T,) containing the Systemic Tau for each window. 
        The first `window_size - 1` elements will be NaN.
    taus_per_module : numpy.ndarray
        2D array of shape (T, N) containing the average Kendall coefficient 
        between module i and all other modules at each step.
    """
    T, N = X.shape
    
    if N < 2:
        raise ValueError("At least 2 components are required to compute Systemic Tau.")
        
    taus_global = np.full(T, np.nan)
    taus_per_module = np.full((T, N), np.nan)
    
    for t in range(window_size - 1, T):
        # Extract sliding window
        window = X[t - window_size + 1 : t + 1, :]
        
        # Rank transformation: replace values with ranks within the window
        ranks = stats.rankdata(window, axis=0)
        
        # Compute pairwise Kendall taus
        tau_matrix = np.zeros((N, N))
        for i, j in itertools.combinations(range(N), 2):
            tau = _kendall_tau_fast(ranks[:, i], ranks[:, j])
            tau_matrix[i, j] = tau
            tau_matrix[j, i] = tau
            
        # Global Systemic Tau (average of upper triangle)
        # N(N-1)/2 pairs
        upper_tri_indices = np.triu_indices(N, k=1)
        taus_global[t] = np.mean(tau_matrix[upper_tri_indices])
        
        # Per-module Tau (average of each row, excluding the diagonal self-correlation)
        for i in range(N):
            # Exclude self by creating a boolean mask
            mask = np.ones(N, dtype=bool)
            mask[i] = False
            taus_per_module[t, i] = np.mean(tau_matrix[i, mask])
            
    return taus_global, taus_per_module


@dataclass
class SystemicTauResult:
    """
    Data class representing the result of a Systemic Tau computation.
    """
    taus_global: np.ndarray
    taus_per_module: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


def systemic_tau(X: np.ndarray, window_size: int = 13, stride: int = 1, method: str = 'kendall', n_jobs: int = -1) -> SystemicTauResult:
    """
    Unified entry point for computing Systemic Tau.
    
    Parameters:
    -----------
    X : numpy.ndarray
        Multivariate time series of shape (T, N).
    window_size : int, optional
        Size of the sliding window (default 13).
    stride : int, optional
        Step size between windows (default 1, other values not yet optimized).
    method : str, optional
        Correlation method to use (default 'kendall'). Currently only 'kendall' is implemented.
    n_jobs : int, optional
        Number of jobs for parallel execution (not yet implemented).
        
    Returns:
    --------
    SystemicTauResult
        A dataclass containing the global taus, per-module taus, and metadata.
    """
    start_time = time.time()
    
    if method != 'kendall':
        raise NotImplementedError(f"Method '{method}' is not implemented yet. Only 'kendall' is supported.")
        
    taus_global, taus_per_module = compute_taus(X, window_size=window_size)
    
    computation_time = time.time() - start_time
    metadata = {
        'window_size': window_size,
        'stride': stride,
        'method': method,
        'n_components': X.shape[1],
        'time_steps': X.shape[0],
        'computation_time_seconds': computation_time
    }
    
    return SystemicTauResult(
        taus_global=taus_global,
        taus_per_module=taus_per_module,
        metadata=metadata
    )
