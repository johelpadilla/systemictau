# Systemic Tau: Roadmap to Version 3.0 (Platform Vision)

Esta hoja de ruta define los objetivos estratégicos y las entregas técnicas concretas para convertir `systemictau` de una librería central (v2.0.0) en una **Plataforma Completa v3.0** (2027). El objetivo principal es dotarla de un núcleo científico optimizado, una interfaz de usuario accesible, validación empírica a escala y *deployment* operativo para casos de uso reales (especialmente vigilancia epidemiológica de dengue y sistemas complejos multivariados).

---

## 1. Plan de Versiones y Entregables Concretos

### v2.1 (Q3 2026, 4-6 semanas)
**Enfoque:** Refinamiento de la API, visualización y cobertura de pruebas.

* **Refactorización mínima de API (sin breaking changes):**
  * Nueva función principal: `systemic_tau(X, window_size=13, stride=1, method='kendall', n_jobs=-1) -> SystemicTauResult`
  * `SystemicTauResult` como *dataclass* con:
    * `taus_global`: `np.ndarray` (shape T,)
    * `taus_per_module`: `np.ndarray` (shape T, N)
    * `metadata`: `dict` (window_size, method, n_components, computation_time, etc.)
  * Mantener funciones legacy (`compute_taus`, `accumulate_time`, etc.) como *wrappers* que llaman a la nueva API por compatibilidad.
* **Módulo `visualization` (dependencia opcional `matplotlib>=3.7`):**
  * `plot_tau_evolution(taus_global, T_series=None, episodes=None, ax=None)`
  * `plot_joint_episodes(episodes, M_series, A_series, ax=None)`
  * `plot_ontological_layers(hp_z, lam, tt, M_series, A_series, t_star=None)`
* **Extender `pyproject.toml`:**
  * Clasificadores completos: *Development Status :: 4 - Beta, Intended Audience :: Science/Research, Topic :: Scientific/Engineering :: Information Analysis, Topic :: Scientific/Engineering :: Physics.*
  * Extras: `visualization`, `full` (incluye pandas, matplotlib, streamlit).
* **Testing y CI:**
  * Añadir 8-10 tests nuevos (ruido 5-20%, series largas T=5000, N=10, comparación con ewstools baseline).
  * Cobertura objetivo: >80% (`pytest-cov`).
  * Integración Continua (CI): Matriz Python 3.9-3.12 + `ruff` lint + reporte de coverage.

### v2.5 (Q4 2026)
**Enfoque:** Integración de datos, utilidades científicas y CLI.

* **Integración con Ecosistemas de Datos:**
  * Integración nativa con `pandas` y `xarray`:
    * `from_dataframe(df, time_col, value_cols, **kwargs) -> SystemicTauResult`
    * `from_xarray(da, **kwargs)`
* **Preprocesamiento Nativo:**
  * Normalización por ventana e imputación de NaNs (opciones: `'drop'`, `'linear'`, `'ffill'`).
* **Módulo `ChaosGenerator`:**
  * Métodos: `logistic_map_coupled(n_steps, n_comp, r=3.8, coupling=0.05, noise=0.0)`
  * `lorenz_coupled`, `rossler_coupled`.
* **Interfaz de Línea de Comandos (CLI) con `typer`:**
  * `systemictau analyze data.csv --window 13 --output results/ --format parquet`
  * `systemictau plot results/systemictau_result.pkl --type tau_evolution`

### v3.0 (Q2-Q3 2027) – Plataforma Completa
**Enfoque:** Arquitectura escalable, dashboards, GIS y automatización en la nube.

* **Arquitectura de Plataforma (`platform/` module):**
  * Core intacto, pero envuelto en una API REST / GraphQL usando **FastAPI** (`/compute/tau`, `/recd/accumulate`, `/layers/joint_episodes`, `/detect/ascent`, `/validate/benchmark`).
  * Frontend interactivo: **Streamlit** dashboard (o Dash/Gradio) con pestañas para Upload, Computation, Layer Analysis, Ontological Ascent Detection y Export.
  * Monitoreo en tiempo real (WebSocket para streaming de datos).
* **Storage y Escalabilidad:**
  * Soporte de escritura/lectura en Parquet, NetCDF y PostgreSQL (opcional para series muy largas).
  * Integración con **Dask** para paralelización masiva (T > 10^5 o N > 50).
* **Módulo `validation` (Benchmarks automáticos):**
  * Comparación contra librerías clásicas (`ewstools`: varianza, autocorrelación, entropía de permutación).
  * Generación de reportes de métricas: *lead time*, *false alarm rate*, AUC para Episodios Conjuntos, Dimensión fractal de T.
* **Integración GIS (Geospatial):**
  * Funciones espaciales: `spatial_tau(gdf, geometry_col, value_cols, **kwargs) -> GeoDataFrame` (hotspots + τs).
  * Exportación directa a Shapefile / GeoJSON para mapeo epidemiológico.

---

## 2. Especificaciones Técnicas Detalladas

### Nuevas Estructuras de Datos
* **`JointEpisode` (TypedDict o dataclass):**
  ```python
  {
      'start': int,
      'end': int,
      'D': int,           # duración
      'M_mean': float,
      'J': float,         # Joint Score
      'J07': float,       # bias-reduced
      'confidence': float # calibrado 0-1
  }
  ```
* **`OntologicalAscentResult`:** `t_star` (int), `t_frob` (int), `max_frob_dist` (float), `t_ks` (int), `max_ks_stat` (float), `method_consensus` (str).

### Parámetros por Defecto Recomendados (Validación Empírica)
* `window_size = 13` (óptimo para constante de Feigenbaum y datos semanales de dengue).
* `theta_chaos = 0.41`, `theta_stable = 0.50`.
* `DELTA = 4.6692016091` (hardcodeado con alta precisión).
* Para `extract_joint_episodes`: `theta_A=0.04`, `D_min=30`, `theta_M=1.0` (ajustables).
* Para hiper-persistencia: `window_size=20`, `run_length >= 7`.

### Rendimiento
* **`compute_taus`**: Integración con **Numba JIT** en bucles de ventanas (objetivo: 5-10x speedup para T=10^4, N=8).
* JAX opcional para diferenciación automática o aceleración en GPU.

---

## 3. Validación Empírica Concreta

**Datasets de referencia incluidos (sintéticos + reales anonimizados):**
1. Mapas logísticos acoplados ($r=3.8$, acoplamiento $0-0.1$, ruido $0-0.2$).
2. Atractores de Lorenz acoplados ($\sigma=10$, $\rho=28$, $\beta=8/3$).
3. **Dengue San Juan** (DengAI + clima, ~927 semanas) – *subset reproducible*.
4. **Dengue Iquitos** equivalente.

**Protocolo de Validación:**
* Calcular $\tau_s$, RECD y Capas.
* Detectar Joint Episodes y $t^*$.
* Comparar *lead time* vs brotes reales (casos > percentil 75-90).
* Reportar: % tiempo en *core-hyper*, número de episodios, fracción de Capa 2, dimensión fractal $D$ de $T$ (Higuchi + Box-counting con IC bootstrap).
* Re-calibrar empíricamente los umbrales (0.41) y la dimensión $D \approx 1.98$ (cotas 1.96-2.01).

---

## 4. Documentación y Reproducibilidad

* **Sphinx + MyST + Napoleon + Mathjax.**
* **Estructura Documental (v3.0):**
  * Getting started (5 min).
  * API reference (autogenerada).
  * **Tutoriales interactivos:** `basic_synthetic.ipynb`, `dengue_real_data.ipynb`, `ontological_ascent_protocol.ipynb`.
  * Reportes de Benchmarks y Validación.
* **Reproducibilidad:** Entorno `conda` determinista (`environment.yml`) y Docker image oficial.
* **Citation:** Integración continua del DOI de Zenodo (v6) y auto-generación del `CITATION.cff`.

---

## 5. Distribución y Operaciones (Deployment)

* **GitHub:** Separación organizativa (ej. org `systemictau`), issue templates (bug, feature, validation) y Discussions para la comunidad.
* **PyPI:** Publicación automática (Trusted Publishing) por GitHub Actions.
* **Docker:** Imagen lista con el core, Streamlit dashboard y backend REST. Ideal para deployments rápidos en Heroku, Railway o VPS (ej. vigilancia de dengue en Ministerios de Salud).
* **Pipeline Dengue PR:** Datos semanales → `systemictau` → Dashboard local → Alertas SMS/Email (Twilio).

---

## 6. Dependencias Estimadas
* **Core (Obligatorias):** `numpy`, `scipy`.
* **Opcionales Recomendadas (`extras`):**
  * `visualization`: `matplotlib`, `seaborn`.
  * `platform`: `pandas`, `xarray`, `streamlit`, `fastapi`, `uvicorn`, `typer`, `numba`, `dask`, `netcdf4`.
  * `validation`: `scikit-learn`, `ruptures`.
  * `gis`: `geopandas`, `rasterio`.

> **Recursos Estimados para v3.0:** 1 Desarrollador Full-Time equivalente + Revisión por pares científica. Scripts optimizados para correr empíricamente en hardware local (laptops) y clústers en la nube.
