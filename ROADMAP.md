# Systemic Tau: Roadmap to Version 2.0

Esta hoja de ruta define los objetivos estratégicos y las mejoras técnicas para llevar el paquete `systemictau` de su actual MVP funcional (v0.1.x) a una herramienta científica de grado de producción (v2.0).

## 1. Objetivos Generales
- **Reproducibilidad y Extensibilidad:** Convertir el paquete en un estándar reproducible.
- **Experiencia de Usuario (UX):** Mejorar drásticamente la documentación y usabilidad.
- **Estabilidad de API:** Evitar *breaking changes* en el futuro.
- **Validación Empírica:** Demostrar umbrales universales y robustez (validado en preprints).
- **Adopción Interdisciplinaria:** Preparar el terreno para ecología, dinámica de sistemas, finanzas y biología computacional.

## 2. Mejoras Fundamentales (Imprescindibles)

### Documentación y UX
- [ ] Documentación completa usando Sphinx + ReadTheDocs o MkDocs.
- [ ] API Reference automática (con `napoleon` o google-style docstrings).
- [ ] Tutoriales paso a paso (instalación, cálculo básico de $\tau_s$, RECD, episodios, fractales).
- [ ] Galería de ejemplos con notebooks que reproduzcan figuras de la *Síntesis Magna*.
- [ ] Ejemplos ejecutables directamente en la documentación.

### Testing y Calidad del Código
- [ ] Suite completa de tests con `pytest`.
- [ ] Tests unitarios exhaustivos para todas las funciones *core* y de *recd*.
- [ ] Tests de integración para validar los umbrales universales (caos, bifurcación).
- [ ] Tests de robustez al ruido (0-20%) y escalabilidad de longitud.
- [ ] Cobertura de código > 85% (`pytest-cov`).
- [ ] Integración Continua (CI/CD) con GitHub Actions (pruebas en Python 3.9–3.12, linting con `ruff`).

### Distribución y Metadata
- [ ] Clasificadores completos en `pyproject.toml` (Beta, Science/Research, Chaos Theory, etc.).
- [ ] Configuración de *Trusted Publishing* en PyPI.

## 3. Nuevas Funcionalidades Clave

### Core / Métricas
- [ ] Refactorización de la API: `systemic_tau(X, method='kendall', window=13, stride=1, n_jobs=-1)`.
- [ ] Soporte avanzado para redes modulares.
- [ ] Comparación con métricas clásicas (Lyapunov, entropía de permutación).
- [ ] `ChaosGenerator`: Generadores de sistemas caóticos (Lorenz, Rössler, Henon) con inyección de ruido.

### RECD y Ontología
- [ ] Módulo `recd` maduro: visualización clara de las tres capas ontológicas.
- [ ] Estimación de dimensión fractal robustecida (Higuchi + Box-counting).

### Visualización y Análisis (Nuevo módulo `visualization`)
- [ ] Heatmaps de $\tau$ pairwise.
- [ ] Evolución temporal superpuesta de $\tau_s$ y $T$ (RECD).
- [ ] Diagramas de fases y atractores.
- [ ] Gráficos de umbrales universales con bandas de confianza.

### Utilidades Avanzadas
- [ ] Integración profunda con `pandas` (DataFrames y series temporales).
- [ ] Preprocesamiento nativo (normalización, imputación de NaNs).
- [ ] CLI (Command Line Interface) básico: `systemictau analyze data.csv --window 13`.

## 4. Mejoras de Rendimiento (Hardware)
- [ ] Optimización con **Numba** o **JAX** (detección automática de GPU).
- [ ] Soporte para chunking o streaming de datos masivos.

## 5. Elementos Estratégicos
- [ ] Ejemplos con datos reales: Ecología (dengue/Aedes), finanzas, clima.
- [ ] Integración con ecosistemas SciPy, statsmodels o tsfresh.
- [ ] `CONTRIBUTING.md` con guías claras para nuevos desarrolladores open-source.
