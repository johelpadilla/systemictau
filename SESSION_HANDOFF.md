# Systemic Tau Studio v4 - Session Handoff (2026-07-03)

## Current Focus
**Studio (web / Streamlit browser app)** — NOT the old Tkinter desktop app.

**Working directory (recommended):**
```bash
cd ~/grok-safe/systemictau
```

**Main files:**
- `src/systemictau/studio/app.py` — Main UI, controls, JSON session Save/Load, Sensitivity UI, Export buttons
- `src/systemictau/studio/analysis.py` — `run_multi_ontological_analysis()` (multi-scale runner, returns scale_results + config with groups + clustering_method)
- `src/systemictau/studio/viz.py` — plots + `create_report_pdf()`
- `src/systemictau/sensitivity.py` — Parameter Sensitivity & Robustness module
- `src/systemictau/exporter.py` — Structured JSON + Excel export (official session format)
- `src/systemictau/desktop/session_manager.py` — Legacy .stausession (no longer used by Studio)
- `src/systemictau/desktop/app.py` — Legacy desktop (maintain compatibility where possible)

## Visualization Baseline (NEW — 2026-07-03)

**`ref-2026-07-03-base` is now the official stable reference for dual plots.**

Location: `versions/ref-2026-07-03-base/`

Key artifacts frozen as baseline:
- `viz.py` — exact source of the rewritten `plot_scale_detail()` (GridSpec, tight hspace=0.018, strong t* band crossing both panels, heavy Δt_k styling, integrated single-figure look).
- `dev_dual_final_local.png`, `dev_dual_final_medium.png`, `dev_dual_final_global.png`
- `report_dual_complete_rewrite.pdf`

**Rule going forward:**
- All changes to dual plots / `plot_scale_detail` must be visually compared against the images in this folder.
- If visualizations regress, restore from `versions/ref-2026-07-03-base/viz.py`.
- The current working `src/systemictau/studio/viz.py` may contain later additions (sensitivity page, clustering docs in PDF). Core dual-plot rendering quality should stay aligned with (or improve upon) this base.

**Decision (2026-07-03):** User selected **Opción C**. 
No code synchronization will be performed. The working `studio/viz.py` stays as-is. 
`ref-2026-07-03-base/` is treated purely as visual + reference baseline for quality validation.

See the README inside `ref-2026-07-03-base/` for full rationale and access instructions.

---

## Recently Completed (this session)

### 1. Parameter Sensitivity & Robustness Analysis
- Created `src/systemictau/sensitivity.py` with `run_parameter_sensitivity()`, stability metrics, quick sweeps.
- Full UI + results table + integration into PDF report.

### 2. Structured Data Export (JSON + Excel) — Multiple rounds of fixes
- Created `src/systemictau/exporter.py` (shared) + desktop shim.
- Proper buttons + preview in Studio Section 5.
- Recommended sheet order and layout:
  - Summary (with Exported at + version + notes)
  - Cluster_Composition (Perspective | Scale | Clustering_Method | Cluster_Name | Variables)
  - Metrics_by_Scale
  - 6 perspective-scale sheets (spatial_*/multivariate_*) with header metrics + Time_Step series
  - Raw_Data (capped)
- **Critical fixes**:
  - Fixed multivariate/Global metrics being incorrectly copied from Medium (duplication bug).
  - Refactored data collection with dedicated `_gather_perspective_scale_data()` using deep copies per perspective.
  - Improved handling of `global_cluster_composition` for "fixed_num" and manual clustering in multivariate perspective.
  - Added validation to detect missing/duplicated Global results.
- Full support for dual perspectives + manual/fixed_num clusters.

### 3. Bugfix: UnboundLocalError in analysis.py
- Fixed `UnboundLocalError: cannot access local variable 'global_cluster_comp'` in `run_multi_ontological_analysis`.
- Moved initialization and capture of cluster composition **after** `used_frames` assignment.
- Added early initialization + fallback logic to ensure composition is always populated for Global scale (including fixed_num path).
- Verified that both manual and fixed_num Global paths now run cleanly and populate `global_cluster_composition`.

### 3. Prior work carried forward
- Explicit Spatial / Multivariate perspectives (analyses dict keyed by view)
- Manual Global + Medium clustering UI
- Basic .stausession support (via shared SessionManager)
- PDF report with clustering documentation + sensitivity page

### 4. Session Persistence — Complete Replacement of .stausession with Structured JSON (v4.x)
- **.stausession (zip) format eliminated** from Studio.
- Official session format is now the **structured JSON** produced by `exporter.py` (`build_structured_export` / `export_to_json`).
- New dedicated functions in Studio:
  - `_save_session_as_json()` — reuses exporter (guarantees both perspectives + full data).
  - `_load_session_from_json()` — uses new `reconstruct_analyses_from_structured_export()` to fully rebuild internal `analyses` dict.
- `reconstruct_analyses_from_structured_export()` (in exporter.py) robustly converts export format back to app format (scale_results, scale_metrics, config with groups/clusters, series).
- UI updated: "Save Session (JSON)" and "Load Session from JSON" file uploader.
- Both perspectives (spatial + multivariate), all 3 scales, manual clusters, series (taus_global, accum_T, dtk), and metrics are fully persisted and restorable.
- After load: user can switch perspectives, generate reports, and export without re-running analysis.
- Legacy SessionManager kept only for desktop compatibility (not used in Studio).

### 5. macOS DMG Packaging (Desktop + Studio)
- Added full macOS distribution support.
- **Desktop app** (CustomTkinter GUI): `dist/SystemicTau-Installer.dmg` (SystemicTau.app)
- **Studio app** (Streamlit): `dist/SystemicTauStudio-Installer.dmg` (SystemicTauStudio.app)
  - Uses `studio_launcher.py` + pywebview: runs Streamlit **internally** (hidden) and displays the full UI inside a **native macOS window** (WebKit). No external browsers (Chrome/Safari) are opened at all. Fully offline, self-contained executable.
- Improved `build_mac.sh`:
  - Always prefers `.venv/bin/python`.
  - Uses `uv pip` when available for robustness.
  - Supports `bash build_mac.sh` (Desktop) and `bash build_mac.sh --studio`.
  - Automatically installs pywebview + Studio runtime packages for --studio builds.
  - Automatic icon handling.
- Added `icons/SystemicTau.icns` (placeholder from project assets; replace for production).
- Updated `SystemicTau.spec` and created `SystemicTauStudio.spec` with proper icon + bundle metadata.
- Streamlit file watcher disabled via `.streamlit/config.toml` (prevents reentrant stdout errors on macOS).
- DMGs include /Applications symlink for easy install.

## Current Status (after recent work)

**Structured Export + JSON Session** is now the single, robust persistence layer for the entire dual-perspective analysis (including clusters and series).

**macOS Distribution** ready:
- Two DMGs in `dist/`:
  - `SystemicTau-Installer.dmg` (Desktop GUI - pure native)
  - `SystemicTauStudio-Installer.dmg` (Studio)
- **Studio is now a real standalone executable** (addresses the browser loop/"host" issue):
  - `studio_launcher.py` uses pywebview → full Studio UI runs inside one native macOS window (WebKit).
  - No Chrome, no Safari, no external browser windows ever.
  - Hidden local server only; 100% offline, no internet or user-managed server required.
- `build_mac.sh` is now venv-first and supports both targets (`--studio`).
- Icon support (`icons/SystemicTau.icns`).
- `studio_launcher.py` (pywebview native window wrapper) + updated specs.

**Visualization baseline** established: `versions/ref-2026-07-03-base/` (Opción C — reference only, no code sync of viz.py).

**Streamlit stability**: File watcher disabled by default to avoid reentrant callback errors on macOS.

## Open Priorities (next after compaction)

- Polish manual Global cluster UI (custom names, better UX).
- Include sensitivity results directly in structured JSON/Excel exports.
- Polish Sensitivity UI + visualizations.
- Broaden sensitivity sweeps.
- Continue using `ref-2026-07-03-base/` as visual reference for any dual-plot work.

## How to Run the App (Studio)
### Development (browser, fast iteration)
```bash
cd ~/grok-safe/systemictau

# Always clear cache after edits
rm -rf src/systemictau/studio/__pycache__

# Run
# Note: file watcher is disabled (.streamlit/config.toml) to avoid reentrant stdout errors
PYTHONPATH=src .venv/bin/streamlit run src/systemictau/studio/app.py
```

### Packaged standalone executable (recommended for macOS end-users)
Double-click `dist/SystemicTauStudio.app` (or the DMG-installed version).
- Opens as a normal native macOS application.
- All UI (including JSON sessions, sensitivity, dual perspectives, reports, exports) works inside the single native window.
- No browsers are launched. Fully offline.

**Recommended data for testing:** `Aedes_Mock_Panel.csv` or `test_panel.csv`

## Current State of Features

| Feature                        | Status                          | Notes |
|--------------------------------|----------------------------------|-------|
| Multi-scale analysis (L/M/G)   | Working                         | Via run_multi_ontological_analysis |
| Multi-perspective (spatial + multivariate) | Working                | analyses dict by view |
| Manual Global / Medium clusters| Implemented                     | UI + passed to runner |
| Session Save / Load            | **Structured JSON (official)**  | .stausession removed. Full dual-perspective restore via JSON. |
| PDF Report                     | Good                            | Includes clustering + sensitivity |
| Sensitivity Analysis           | Fully implemented (UI + core)   | Sweeps + stability |
| Structured Export (JSON/Excel) | **Polished + Fixed**            | Summary + Cluster_Composition + Metrics_by_Scale + 6 perspective-scale sheets. Fixed multivariate/Global duplication bug + improved fixed_num cluster composition. |
| macOS Packaging (DMG)          | **Updated**                     | Desktop (pure native) + Studio DMG. Studio now uses pywebview for a real standalone executable: full Studio UI inside a native macOS window, zero external browser launches, fully offline, no visible server. |

## Open / Next Tasks (priority order)

1. Polish Manual Global cluster UI (custom cluster names instead of only "Macro_1", better UX for remaining variables).

2. Include sensitivity results directly inside structured JSON/Excel session exports.

3. Polish Sensitivity UI (better progress, visualizations inside the app).

4. Broaden sensitivity sweeps (agg_method, RECD toggle, etc.).

5. Maintain visual quality against `ref-2026-07-03-base/` for any dual-plot changes.

## Important Notes
- **Primary focus remains the Studio** (`src/systemictau/studio/`)
- SessionManager is shared — changes must not break desktop completely, but studio is the testbed/verification target.
- After code changes: `rm -rf src/systemictau/studio/__pycache__`
- The project root is `~/grok-safe/systemictau`
- `sensitivity.py` and `exporter.py` are ready shared modules.

## When Resuming
Paste the full content of this `SESSION_HANDOFF.md` (and optionally CONVERSATION_HANDOFF + NEXT_TASKS) and say:

"Resume work on Systemic Tau Studio.

**Major changes:**
- .stausession removed — sessions use structured JSON (exporter + reconstruct_analyses_from_structured_export).
- macOS DMGs ready for both Desktop (pure native) and Studio.
- Studio now ships as a **true standalone executable app** (no browser, no external host connection problems):
  - Uses pywebview in `studio_launcher.py` → complete Studio UI inside one native macOS window.
  - Fully offline, self-contained, no Chrome/Safari spawns.
- build_mac.sh improved (venv-first, --studio flag, auto-installs pywebview + studio deps, icon support).
- Added/updated studio_launcher.py + SystemicTauStudio.spec + icons/SystemicTau.icns.
- Streamlit file watcher disabled (.streamlit/config.toml).

Visualization baseline: versions/ref-2026-07-03-base/ (Opción C).

To build:
  bash build_mac.sh
  bash build_mac.sh --studio

Run dev Studio (browser):
  PYTHONPATH=src .venv/bin/streamlit run src/systemictau/studio/app.py

Packaged Studio app:
  Double-click dist/SystemicTauStudio.app (or install from DMG)"

Generated: 2026-07-03 (updated)
