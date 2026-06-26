import numpy as np
import systemictau as st

def logistic_map(n_steps, r, x0=0.5):
    x = np.zeros(n_steps)
    x[0] = x0
    for i in range(1, n_steps):
        x[i] = r * x[i-1] * (1 - x[i-1])
    return x

def main():
    # 1. Generate synthetic data (coupled logistic maps near Feigenbaum accumulation point)
    np.random.seed(42)
    n_steps = 2000
    n_components = 4
    
    # We create slightly different logistic maps to simulate coupling/noise
    r_val = 3.8
    X = np.zeros((n_steps, n_components))
    for i in range(n_components):
        # Adding a small perturbation to initial conditions
        X[:, i] = logistic_map(n_steps, r_val, x0=0.1 + i*0.05)
    
    print(f"Generated data shape: {X.shape}")
    
    # 2. Compute Systemic Tau
    taus_global, taus_per_module = st.compute_taus(X, window_size=13)
    
    # Check valid values (dropping NaNs from the initial window)
    valid_taus = taus_global[~np.isnan(taus_global)]
    print(f"Computed Systemic Tau. Mean |tau|: {np.mean(np.abs(valid_taus)):.3f}")
    
    # 3. Compute RECD Time
    T_series, dtk_series, gate_series, depths = st.accumulate_time(taus_global)
    print(f"Total Extramental Time T accumulated: {T_series[-1]:.4f}")
    
    # 4. Three-Layer Ontology Detections
    # Capa 1
    hp_z, core_hyper = st.hyper_persistence(taus_global)
    lam, tt = st.rolling_rqa(taus_global)
    M_series = st.critical_mass_metric(hp_z, lam, tt)
    
    print(f"Fraction of time in core-hyper: {np.mean(core_hyper):.1%}")
    
    # Capa 2
    A_series = st.compute_antisynchronization(taus_per_module)
    episodes = st.extract_joint_episodes(A_series, M_series, theta_A=0.05, D_min=10)
    print(f"Detected {len(episodes)} Joint Episodes.")
    
    # Capa 3
    # Simulating a structural change at step 1000
    t_frob, max_dist = st.detect_reorganization_frob(taus_per_module)
    t_ks, max_ks = st.detect_reorganization_ks(dtk_series)
    t_star = st.consensus_transition(t_frob, t_ks)
    print(f"Detected Capa 3 reorganization at t* = {t_star} (KS={max_ks:.3f})")
    
    # 5. Fractal Dimension
    # We expect D around 1.98 for purely chaotic runs
    if T_series[-1] > 0:
        D = st.estimate_higuchi_dimension(T_series, k_max=20)
        print(f"Estimated Higuchi Fractal Dimension of T: {D:.3f} (Theoretical ~ 1.98)")

if __name__ == "__main__":
    main()
