# Systemic Tau Studio - Quick Next Tasks

## Priority 1 (Do this first when resuming after compaction)
- [x] **macOS DMG Packaging (Desktop + Studio)**
  - Two installers: `SystemicTau-Installer.dmg` (CustomTkinter desktop) and `SystemicTauStudio-Installer.dmg` (Streamlit).
  - `build_mac.sh` now venv-first, uses uv when available, supports `--studio` flag, auto-installs pywebview.
  - `studio_launcher.py` now uses pywebview: launches Studio as a **real standalone native macOS executable**.
    - One native window containing the entire Studio UI.
    - Zero external browser windows (no more Chrome + Safari loops or "host" connection failures).
    - Fully offline / no servers visible to the user.
  - Icon support via `icons/SystemicTau.icns`.
  - Updated specs and dmg_settings.

- [x] **Replace .stausession with Structured JSON Session Save/Load (v4.x)**
  - .stausession (zip) completely removed from Studio.
  - Sessions now use the structured JSON from the exporter (`export_to_json` / `build_structured_export`).
  - New `reconstruct_analyses_from_structured_export()` in exporter.py for robust roundtrip.
  - Full support: both perspectives, 3 scales each, series, manual clusters per perspective.

- [x] **Multivariate Global fix in Structured Export**
  - `_gather_perspective_scale_data()` + `get_scale_results(perspective, scale)` with deep copies.
  - Strong validation + improved cluster composition for fixed_num/manual.

- [x] **Visualization baseline**
  - `versions/ref-2026-07-03-base/` declared new stable reference (Opción C — no code sync).

## Recently Completed (marking progress)
- [x] Full replacement of .stausession with Structured JSON session save/load (2026-07-03)
- [x] macOS DMG packaging (Desktop + Studio) via improved build_mac.sh
- [x] Parameter Sensitivity & Robustness module + UI + PDF integration
- [x] Structured Data Export (JSON + multi-sheet Excel) + major per-perspective fixes
- [x] Multivariate Global duplication fix + robust gatherer
- [x] New visualization baseline (`ref-2026-07-03-base`)
- [x] Studio launcher (`studio_launcher.py`) rewritten for pywebview native macOS app (solves external browser problem)
- [x] Icon support (icons/SystemicTau.icns) and .streamlit/config.toml for stability

## Priority 2
- [ ] Polish manual Global cluster UI (custom cluster names, better UX)
- [ ] Include sensitivity results directly in structured JSON/Excel exports
- [ ] Polish Sensitivity UI + add visualizations
- [ ] Broaden sensitivity parameter support
- [ ] Maintain alignment with `ref-2026-07-03-base/` for dual plots

## Visualization Reference
- **New base (2026-07-03)**: `versions/ref-2026-07-03-base/`
  - Use the images (`dev_dual_final_*.png`) and `viz.py` as the quality bar for any dual-plot work.
  - Core `plot_scale_detail` implementation + styling must match or beat this baseline.
- **Current status:** Opción C chosen. Working `studio/viz.py` left as-is; base is reference only.

## Useful Commands
```bash
cd ~/grok-safe/systemictau

# After any code change
rm -rf src/systemictau/studio/__pycache__

# Run the Studio app
# Note: file watcher disabled in .streamlit/config.toml (avoids reentrant errors)
PYTHONPATH=src .venv/bin/streamlit run src/systemictau/studio/app.py
```

## Key Files
- `src/systemictau/exporter.py`               ← main exporter logic (gatherer + cluster composition)
- `src/systemictau/studio/analysis.py`        ← run_multi_ontological_analysis + global_cluster_comp
- `src/systemictau/studio/app.py`             ← UI + export/save/load wrappers
- `src/systemictau/desktop/session_manager.py`

See `SESSION_HANDOFF.md` for latest state.

Generated: 2026-07-03 (updated)
