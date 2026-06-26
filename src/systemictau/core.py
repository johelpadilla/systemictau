import numpy as np
import scipy.stats as stats
import itertools

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
