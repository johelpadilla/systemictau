# Systemic Tau & Discrete Extramental Clock (RECD)

[![PyPI version](https://badge.fury.io/py/systemictau.svg)](https://badge.fury.io/py/systemictau)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**`systemictau`** is a Python package implementing the mathematical and ontological framework of the **Systemic Tau paradigm** and the **Discrete Extramental Clock (RECD)**, developed by Dr. Johel Padilla-Villanueva, DrPH.

This package offers a novel, non-reductive approach for time series analysis in complex systems, shifting from classical variance-based early-warning signals to purely **ordinal** observables. It provides tools for detecting structural reorganization, relational coherence, and ontological ascent in multivariate dynamics.

---

## 📖 Core Concepts

The package operationalizes the three-layer ontological framework detailed in the *Magna Synthesis*:

### **Capa 1 (Local Intensification)**
Measures local persistence through hyper-persistence of ordinal states and structural trapping using Recurrence Quantification Analysis (RQA).

### **Capa 2 (Relational Coherence)**
Identifies *Joint Episodes* (relational kairoi) by measuring anti-synchronization patterns across system modules and critical mass metrics.

### **Capa 3 (Ontological Ascent)**
Detects the exact moment of global structural reorganization through Kolmogorov-Smirnov contrasts and Frobenius norm shifts, indicating emergence of a new layer of organization.

---

## 🚀 Installation

### From PyPI (Recommended)
```bash
pip install systemictau
```

### From Source
```bash
git clone https://github.com/johelpadilla/systemictau
cd systemictau
pip install -e .
```

---

## 💡 Quick Start

```python
import numpy as np
import systemictau as st

# 1. Load or generate multivariate time series data
# X = np.array([...]) # Shape: (T_steps, N_components)
np.random.seed(42)
X = np.random.randn(500, 4)

# 2. Compute Systemic Tau over sliding windows
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
```

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive usage documentation
- **[API Reference](docs/API.md)** - Complete function reference
- **[Theory](docs/THEORY.md)** - Mathematical foundations and proofs
- **[Examples](examples/)** - Worked examples and case studies

---

## 🔬 Applications

### Public Health Surveillance
**Dengue Early-Warning System** - See [`tau-sistemic-dengue-ews`](https://github.com/johelpadilla/tau-sistemic-dengue-ews) for a real-world application using this framework.

### Complex Systems Analysis
Use Systemic Tau to detect:
- Regime shifts and critical transitions
- Structural reorganization in networks
- Relational coherence in coupled systems
- Early-warning signals for system collapse

---

## 📦 macOS Desktop Application

For users who prefer a graphical interface:
- **Download**: [Systemic Tau v3.0 (macOS)](https://github.com/johelpadilla/systemictau/releases)
- **User Guide**: [Desktop App Documentation](docs/DESKTOP_APP.md)

---

## 🔗 Related Repositories

| Repository | Purpose | Access |
|---|---|---|
| [`tau-sistemic`](https://github.com/johelpadilla/tau-sistemic) | Core theory (Spanish) | Public |
| [`tau-sistemic-dengue-ews`](https://github.com/johelpadilla/tau-sistemic-dengue-ews) | Applied case study | Public |
| [`principle-of-ontological-ascent`](https://github.com/johelpadilla/principle-of-ontological-ascent) | Foundational theory | Public |
| [`systemictau_v4`](https://github.com/johelpadilla/systemictau_v4) | Development branch | Private |

---

## 📖 Citation

If you use this package in your research, please cite:

```bibtex
@software{padilla2026systemic,
  author = {Padilla-Villanueva, Johel},
  title = {Systemic Tau: Python Implementation of RECD Framework},
  year = {2026},
  url = {https://github.com/johelpadilla/systemictau},
  note = {Version 2.x - PyPI}
}
```

For the foundational theoretical work:

```bibtex
@unpublished{padilla2026synthesis,
  author = {Padilla-Villanueva, Johel},
  title = {Síntesis Magna del Tau Sistémico},
  year = {2026},
  howpublished = {Zenodo},
  doi = {10.5281/zenodo.20576241},
  note = {Version 6}
}
```

---

## 📄 License

- **Code**: MIT License - see [LICENSE](LICENSE) file
- **Theory & Manuscripts**: CC-BY 4.0 - see [LICENSE.THEORY](LICENSE.THEORY)

---

## 👤 Author

**Dr. Johel Padilla-Villanueva, DrPH**
- 🎓 Universidad de Puerto Rico
- 📧 [Academic Site](https://github.com/johelpadilla/academic-site)
- 🔬 Research: Complex Systems, Public Health, Ontology

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📞 Support

- **Issues & Bug Reports**: [GitHub Issues](https://github.com/johelpadilla/systemictau/issues)
- **Documentation**: [GitHub Wiki](https://github.com/johelpadilla/systemictau/wiki)
- **Academic Contact**: See [academic-site](https://github.com/johelpadilla/academic-site)

---

**Last Updated**: 2026  
**Current Version**: 2.x (PyPI) | 3.0+ (Development)
