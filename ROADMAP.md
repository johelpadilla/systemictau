# Systemic Tau: Roadmap to Version 3.0 (Platform Vision)

This roadmap defines the strategic objectives and concrete technical deliverables to transition `systemictau` from a core library (v2.0.1) into a **Complete Platform v3.0** (2027). The main goal is to endow it with an optimized scientific core, an accessible user interface, large-scale empirical validation, and operational deployment for real-world use cases (especially dengue epidemiological surveillance and multivariate complex systems).

---

## 1. Version Plan and Concrete Deliverables

### v2.1 (Q3 2026, 4-6 weeks)
**Focus:** API refinement, visualization, and test coverage.

* **Minimal API Refactoring (no breaking changes):**
  * New main function: `systemic_tau(X, window_size=13, stride=1, method='kendall', n_jobs=-1) -> SystemicTauResult`
  * `SystemicTauResult` as a *dataclass* with:
    * `taus_global`: `np.ndarray` (shape T,)
    * `taus_per_module`: `np.ndarray` (shape T, N)
    * `metadata`: `dict` (window_size, method, n_components, computation_time, etc.)
  * Keep legacy functions (`compute_taus`, `accumulate_time`, etc.) as wrappers calling the new API for backward compatibility.
* **`visualization` Module (optional dependency `matplotlib>=3.7`):**
  * `plot_tau_evolution(taus_global, T_series=None, episodes=None, ax=None)`
  * `plot_joint_episodes(episodes, M_series, A_series, ax=None)`
  * `plot_ontological_layers(hp_z, lam, tt, M_series, A_series, t_star=None)`
* **Extend `pyproject.toml`:**
  * Comprehensive classifiers: *Development Status :: 4 - Beta, Intended Audience :: Science/Research, Topic :: Scientific/Engineering :: Information Analysis, Topic :: Scientific/Engineering :: Physics.*
  * Extras: `visualization`, `full` (includes pandas, matplotlib, streamlit).
* **Testing and CI:**
  * Add 8-10 new tests (5-20% noise, long series T=5000, N=10, comparison with `ewstools` baseline).
  * Target coverage: >80% (`pytest-cov`).
  * Continuous Integration (CI): Update `.github/workflows/python-app.yml` with Python 3.9-3.12 matrix + `ruff` linting + coverage report.

### v2.5 (Q4 2026)
**Focus:** Data integration, scientific utilities, and CLI.

* **Data Ecosystems Integration:**
  * Native integration with `pandas` and `xarray`:
    * `from_dataframe(df, time_col, value_cols, **kwargs) -> SystemicTauResult`
    * `from_xarray(da, **kwargs)`
* **Native Preprocessing:**
  * Window-based normalization and NaN imputation (options: `'drop'`, `'linear'`, `'ffill'`).
* **`ChaosGenerator` Module:**
  * Methods: `logistic_map_coupled(n_steps, n_comp, r=3.8, coupling=0.05, noise=0.0)`
  * `lorenz_coupled`, `rossler_coupled`.
* **Command Line Interface (CLI) with `typer`:**
  * `systemictau analyze data.csv --window 13 --output results/ --format parquet`
  * `systemictau plot results/systemictau_result.pkl --type tau_evolution`

### v3.0 (Q2-Q3 2027) – Complete Platform
**Focus:** Scalable architecture, dashboards, GIS, and cloud automation.

* **Platform Architecture (`platform/` module):**
  * Core untouched, but wrapped in a REST / GraphQL API using **FastAPI** (`/compute/tau`, `/recd/accumulate`, `/layers/joint_episodes`, `/detect/ascent`, `/validate/benchmark`).
  * Interactive frontend: **Streamlit** dashboard (or Dash/Gradio) with tabs for Upload, Computation, Layer Analysis, Ontological Ascent Detection, and Export.
  * Real-time monitoring (WebSocket for data streaming).
* **Storage and Scalability:**
  * Read/write support for Parquet, NetCDF, and PostgreSQL (optional for very long series).
  * Integration with **Dask** for massive parallelization (T > 10^5 or N > 50).
* **`validation` Module (Automated Benchmarks):**
  * Comparison against classic libraries (`ewstools`: variance, autocorrelation, permutation entropy).
  * Metric report generation: *lead time*, *false alarm rate*, AUC for Joint Episodes, Fractal dimension of T.
* **GIS Integration (Geospatial):**
  * Spatial functions: `spatial_tau(gdf, geometry_col, value_cols, **kwargs) -> GeoDataFrame` (hotspots + τs).
  * Direct export to Shapefile / GeoJSON for epidemiological mapping.

---

## 2. Detailed Technical Specifications

### New Data Structures
* **`JointEpisode` (TypedDict or dataclass):**
  ```python
  {
      'start': int,
      'end': int,
      'D': int,           # duration
      'M_mean': float,
      'J': float,         # Joint Score
      'J07': float,       # bias-reduced
      'confidence': float # calibrated 0-1
  }
  ```
* **`OntologicalAscentResult`:** `t_star` (int), `t_frob` (int), `max_frob_dist` (float), `t_ks` (int), `max_ks_stat` (float), `method_consensus` (str).

### Recommended Default Parameters (Empirical Validation)
* `window_size = 13` (optimal for Feigenbaum constant and weekly dengue data).
* `theta_chaos = 0.41`, `theta_stable = 0.50`.
* `DELTA = 4.6692016091` (hardcoded with high precision).
* For `extract_joint_episodes`: `theta_A=0.04`, `D_min=30`, `theta_M=1.0` (adjustable).
* For hyper-persistence: `window_size=20`, `run_length >= 7`.

### Performance
* **`compute_taus`**: **Numba JIT** integration in window loops (target: 5-10x speedup for T=10^4, N=8).
* Optional JAX for automatic differentiation or GPU acceleration in large validations.

---

## 3. Concrete Empirical Validation

**Reference Datasets to include (synthetic + anonymized real data):**
1. Coupled logistic maps ($r=3.8$, coupling $0-0.1$, noise $0-0.2$).
2. Coupled Lorenz attractors ($\sigma=10$, $\rho=28$, $\beta=8/3$).
3. **San Juan Dengue** (DengAI + climate, ~927 weeks) – *reproducible subset*.
4. **Iquitos Dengue** equivalent.

**Validation Protocol:**
* Compute $\tau_s$, RECD, and Layers.
* Detect Joint Episodes and $t^*$.
* Compare *lead time* vs real outbreaks (cases > 75-90th percentile).
* Report: % time in *core-hyper*, number of episodes, global fraction of Layer 2, fractal dimension $D$ of $T$ (Higuchi + Box-counting with bootstrap CI).
* Empirically re-calibrate universal thresholds (0.41) and the $D \approx 1.98$ dimension (bounds 1.96-2.01).

---

## 4. Documentation and Reproducibility

* **Sphinx + MyST + Napoleon + Mathjax.**
* **Documentary Structure (v3.0):**
  * Getting started (5 min).
  * API reference (auto-generated).
  * **Interactive tutorials:** `basic_synthetic.ipynb`, `dengue_real_data.ipynb`, `ontological_ascent_protocol.ipynb`.
  * Benchmarks & Validation reports (updatable).
* **Reproducibility:** Deterministic `conda` environment (`environment.yml`) and official Docker image.
* **Citation:** Keep Zenodo DOI (v6) + auto-generate `CITATION.cff` for the package.

---

## 5. Distribution and Operations (Deployment)

* **GitHub:** Organizational separation (e.g., `systemictau` org), issue templates (bug, feature, validation), and Discussions for the community.
* **PyPI:** Automated releases (Trusted Publishing) via GitHub Actions.
* **Docker:** Image ready with the core, Streamlit dashboard, and REST backend. Ideal for quick deployments on Heroku, Railway, or VPS (e.g., dengue surveillance in Ministries of Health).
* **Dengue PR Pipeline:** Weekly data → `systemictau` → Local/private dashboard → SMS/Email alerts (via Twilio or similar, optional).

---

## 6. Dependencies and Resources
* **Core (Mandatory):** `numpy`, `scipy` (already existing).
* **Recommended Optionals (`extras`):**
  * `visualization`: `matplotlib`, `seaborn`
  * `platform`: `pandas`, `xarray`, `streamlit`, `fastapi`, `uvicorn`, `typer`, `numba`, `dask`, `netcdf4`
  * `validation`: `scikit-learn` (for metrics), `ruptures` (change point baseline)
  * `gis`: `geopandas`, `rasterio` (extra only)

> **Estimated Resources for v3.0:** 1 Full-Time equivalent developer + scientific peer review (you + collaborators). Optimized compute scripts to run empirically on local laptops (Numba) or small cloud servers (Dask local). Real testing access to complete dengue series or calibrated synthetic data.
