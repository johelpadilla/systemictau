# Conversation Handoff - Systemic Tau Studio (2026-07-03)

**Date:** 2026-07-03  
**Focus:** Continuing development of the **Studio** (Streamlit) version in the grok-safe workspace.

## Context at Start of This Session
- Project consolidated in `~/grok-safe/systemictau` (full systemictau + Publicaciones copied from previous locations).
- Prior state included basic Save/Load, Manual Global clustering, improved PDF.
- User asked to review latest work, copy "lo ultimo", then confirmed context.
- User pasted plans for Sensitivity, Structured Export, Session fixes (first .stausession, then full JSON replacement).
- Said "arrancamos directamente".
- Multiple "crea handoff" / "handoff update" requests.
- Latest prompt: "Replace .stausession with Structured JSON Load/Save".

## What Was Implemented

### 1. Parameter Sensitivity & Robustness Analysis
**Files:**
- New: `src/systemictau/sensitivity.py`
- `src/systemictau/studio/app.py` — expander, run button, st.session_state.sensitivity_report, table display
- `src/systemictau/studio/viz.py` — extended `create_report_pdf` with sensitivity page

### 2. Structured Data Export (JSON + Excel) — Significant polishing
**Files:**
- `src/systemictau/exporter.py` (main logic)
- `src/systemictau/desktop/exporter.py` (shim)
- Multiple iterations:
  - Professional sheet layout (Summary, Cluster_Composition, Metrics_by_Scale, 6 named scale sheets, Raw_Data).
  - **Key fix**: Resolved multivariate/Global copying values from Medium (duplication bug in mean_tau, t_star, recd_T_final, etc.).
  - Introduced `_gather_perspective_scale_data()` for clean, independent per-perspective records.
  - Improved cluster composition handling for "fixed_num" and manual clustering on multivariate Global.
  - Added validation + better number formatting.

### 3. Bug Fix: UnboundLocalError
- Fixed crash in `studio/analysis.py` (`global_cluster_comp` referenced before assignment).
- Reordered initialization/capture of cluster composition after `used_frames`.
- Added robust fallback so composition is always available for Global scale.
- Both manual and fixed_num paths now work cleanly.

### 4. Session Persistence — Structured JSON (replaces .stausession)
- .stausession format completely removed from Studio.
- Sessions now saved/loaded using the structured JSON from the exporter.
- Added `reconstruct_analyses_from_structured_export()` for robust state reconstruction.
- New Studio functions: `_save_session_as_json()` and `_load_session_from_json()`.
- Full support for both perspectives + all scales + manual clusters + series after load.
- UI replaced with JSON save button + JSON file uploader.

## Key Commands
```bash
cd ~/grok-safe/systemictau
rm -rf src/systemictau/studio/__pycache__
# Note: file watcher disabled (.streamlit/config.toml)
PYTHONPATH=src .venv/bin/streamlit run src/systemictau/studio/app.py
```

## Current Priorities (for next session after compaction)
See `SESSION_HANDOFF.md` and `NEXT_TASKS.md`.

**New important baseline:**
- `versions/ref-2026-07-03-base/` = official new base for dual plots and `plot_scale_detail`.
- Decision: Opción C (reference only, no code sync).

**Major changes:**
- .stausession eliminated — sessions use structured JSON.
- macOS DMGs ready:
  - Desktop: dist/SystemicTau-Installer.dmg (pure native)
  - Studio: dist/SystemicTauStudio-Installer.dmg
- **Studio packaging changed to solve browser spawn/loop problem**:
  - `studio_launcher.py` now uses pywebview.
  - The app opens as a single native macOS window containing the full Studio (Streamlit UI).
  - No external browsers, no "host" connection issues from outside, fully self-contained + offline.
- build_mac.sh improved (venv-first + uv, supports --studio, auto pywebview install for studio, icons).
- studio_launcher.py + SystemicTauStudio.spec updated for pywebview.
- Icon: icons/SystemicTau.icns
- .streamlit/config.toml (disables watcher to avoid reentrant errors).

Main open items: Polish manual Global UI, include sensitivity in exports, sensitivity UI polish.

## How to Resume After Compaction
Paste the content of **SESSION_HANDOFF.md** (latest version) + this file and say:

"Resume work on Systemic Tau Studio.

.stausession removed — sessions use structured JSON.
macOS DMGs ready (Desktop + Studio).
Studio now uses pywebview launcher → native window, no external browsers, fully offline executable (fixes the perpetual Chrome/Safari loop + host connection issue).
build_mac.sh improved (venv-first, --studio, pywebview install).
Visualization reference: versions/ref-2026-07-03-base/ (Opción C).

Other: multivariate Global export fixes, sensitivity, Streamlit watcher fix.

To build DMGs:
  bash build_mac.sh
  bash build_mac.sh --studio

Packaged Studio: double-click dist/SystemicTauStudio.app"

Generated: 2026-07-03 (updated)
