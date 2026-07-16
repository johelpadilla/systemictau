# Systemic Tau & Discrete Extramental Clock (RECD)

[![PyPI version](https://badge.fury.io/py/systemictau.svg)](https://pypi.org/project/systemictau/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**`systemictau`** implements the **Systemic Tau** paradigm and the **Discrete Extramental Clock (RECD)** for ordinal multivariate time-series analysis (early-warning, regime reorganization, multi-scale structure).

**Current library version:** 4.6.0

## Installation

```bash
pip install systemictau
# Level-3 nested ordinal RECD / continuous excess³:
pip install "systemictau[nested]"   # pulls nested-recd>=0.2
```

From source:

```bash
git clone https://github.com/johelpadilla/systemictau
cd systemictau
pip install -e ".[nested,dev]"
```

## Two RECD notions (do not confuse)

| Name | API | What it is |
|------|-----|------------|
| **Gate RECD** | `compute_recd_increments`, `accumulate_time` | Clock from **τ_s** + Feigenbaum gate |
| **Nested ordinal RECD / excess³** | `compute_nested_recd` → [`nested-recd`](https://pypi.org/project/nested-recd/) | Φ₁–Φ₃ on Bandt–Pompe; **excess³ = 0.6·Syn + 0.4·Surp** primary Level-3 |

Canonical Level-3 methods: [DOI 10.5281/zenodo.21385937](https://doi.org/10.5281/zenodo.21385937) · [github.com/johelpadilla/excess3](https://github.com/johelpadilla/excess3)

## Quick start

```python
import numpy as np
import systemictau as st

np.random.seed(42)
X = np.random.randn(500, 4)

# Systemic Tau
taus_global, taus_per_module = st.compute_taus(X, window_size=13)

# Gate RECD
T_series, dtk_series, gate_series, depths = st.accumulate_time(taus_global)

# Nested ordinal RECD / continuous excess³ (requires nested-recd)
if st.has_nested_recd():
    nested = st.compute_nested_recd(X, tau_s=taus_global, m=3, theta3=0.10)
    print("mean excess³:", float(np.nanmean(nested["excess3"])))

# Full pipeline with optional Level-3
res = st.run_full_analysis(X, window_size=13, compute_nested_recd=True)
print("t* =", res.t_star)
if res.nested_recd_results:
    print("mean excess³:", res.nested_recd_results["mean_excess3"])
```

## Studio (optional)

```bash
pip install "systemictau[studio]"
systemictau-studio
# or: PYTHONPATH=src streamlit run src/systemictau/studio/app.py
```

## Related packages

| Project | Role |
|---------|------|
| [`nested-recd`](https://pypi.org/project/nested-recd/) | Canonical Φ₁–Φ₃ + excess³ core |
| [`excess3`](https://github.com/johelpadilla/excess3) | Methods + intro ES + primer |
| [`systemictau-web`](https://github.com/johelpadilla/systemictau-web) | Streamlit analytical app |

## Citation

> Padilla-Villanueva, Johel. (2026). *Síntesis Magna del Tau Sistémico*. Zenodo. DOI: [10.5281/zenodo.20576241](https://doi.org/10.5281/zenodo.20576241)

For excess³ / Level-3 claims, also cite:

> Padilla-Villanueva, J. (2026). *excess³* methods. DOI: [10.5281/zenodo.21385937](https://doi.org/10.5281/zenodo.21385937)

## License

MIT © Johel Padilla-Villanueva  
ORCID: [0000-0002-5797-6931](https://orcid.org/0000-0002-5797-6931)
