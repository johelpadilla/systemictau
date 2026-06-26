Tutorial
========

This section provides a quick overview of how to use the `systemictau` package.

We highly recommend following our interactive Jupyter Notebook tutorial, which is available in the repository root as `basic_tutorial.ipynb`.

Basic Usage
-----------

Below is a snippet demonstrating the core API:

.. code-block:: python

    import numpy as np
    import systemictau as st

    # 1. Provide your multivariate time series data
    # X = np.array([...]) # Shape: (T_steps, N_components)
    np.random.seed(42)
    X = np.random.randn(500, 4)

    # 2. Compute the Systemic Tau over sliding windows
    taus_global, taus_per_module = st.compute_taus(X, window_size=13)

    # 3. Accumulate the Discrete Extramental Time (RECD)
    T_series, dtk_series, gate_series, depths = st.accumulate_time(taus_global)

    # 4. Extract Relational Windows (Joint Episodes)
    hp_z, core_hyper = st.hyper_persistence(taus_global)
    lam, tt = st.rolling_rqa(taus_global)
    M_series = st.critical_mass_metric(hp_z, lam, tt)

    A_series = st.compute_antisynchronization(taus_per_module)
    episodes = st.extract_joint_episodes(A_series, M_series)

    # 5. Detect Capa 3 Reorganization (Ontological Ascent)
    t_frob, max_dist = st.detect_reorganization_frob(taus_per_module)
    t_ks, max_ks = st.detect_reorganization_ks(dtk_series)
    t_star = st.consensus_transition(t_frob, t_ks)

    print(f"Capa 3 Transition detected at t* = {t_star}")
