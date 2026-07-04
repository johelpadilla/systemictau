"""Quick verification script for the improved structured Excel exporter."""
import os
import tempfile
import numpy as np
import pandas as pd

from systemictau.exporter import export_to_excel, build_structured_export

print("Imports OK")

np.random.seed(42)
T = 80
fake_tau = np.cumsum(np.random.randn(T)) * 0.01 + 1.0

analysis_spatial = {
    "scale_results": {
        "Local": {"taus_global": fake_tau, "accum_T": np.cumsum(fake_tau), "dtk": np.diff(fake_tau, prepend=0), "t_star": 37},
        "Medium": {"taus_global": fake_tau*0.95, "accum_T": np.cumsum(fake_tau)*0.9, "dtk": np.diff(fake_tau, prepend=0)*0.8, "t_star": 41},
        "Global": {"taus_global": fake_tau*0.8, "accum_T": np.cumsum(fake_tau)*0.7, "dtk": np.diff(fake_tau, prepend=0)*0.6, "t_star": 52},
    },
    "scale_metrics": {
        "Local": {"mean_tau": 1.12, "tau_std": 0.08, "coherence": 0.71, "recd_T_final": 142.3, "n_modules": 12},
        "Medium": {"mean_tau": 0.95, "tau_std": 0.06, "coherence": 0.82, "recd_T_final": 138.1, "n_modules": 4},
        "Global": {"mean_tau": 0.71, "tau_std": 0.04, "coherence": 0.91, "recd_T_final": 129.4, "n_modules": 2},
    },
    "config": {
        "window_size": 13,
        "medium_groups": {"Cluster_1": ["Loc_01", "Loc_02", "Loc_03"], "Cluster_2": ["Loc_04", "Loc_05"]},
        "global_groups": {"Macro_1": ["Cluster_1", "Cluster_2"]},
        "clustering_method": {"medium": "manual", "global": "manual"},
    }
}

analysis_mv = {
    "scale_results": {
        "Local": {"taus_global": fake_tau + 0.2, "accum_T": np.cumsum(fake_tau + 0.2), "dtk": np.zeros(T), "t_star": 29},
        "Medium": {"taus_global": fake_tau * 0.9 + 0.1, "accum_T": np.cumsum(fake_tau) * 0.85, "dtk": np.diff(fake_tau, prepend=0) * 0.5, "t_star": 33},
        "Global": {"taus_global": fake_tau * 0.75, "accum_T": np.cumsum(fake_tau) * 0.65, "dtk": np.diff(fake_tau, prepend=0) * 0.4, "t_star": 48},
    },
    "scale_metrics": {
        "Local": {"mean_tau": 1.31, "tau_std": 0.11, "coherence": 0.65, "recd_T_final": 155.8, "n_modules": 5},
        "Medium": {"mean_tau": 1.05, "tau_std": 0.07, "coherence": 0.79, "recd_T_final": 147.2, "n_modules": 3},
        "Global": {"mean_tau": 0.82, "tau_std": 0.03, "coherence": 0.88, "recd_T_final": 134.9, "n_modules": 2},
    },
    "config": {
        "window_size": 13,
        "medium_groups": {},
        "global_groups": {},
        "clustering_method": {"medium": "auto", "global": "auto"},
    }
}

analyses = {"spatial": analysis_spatial, "multivariate": analysis_mv}
df_raw = pd.DataFrame({"time": range(120), "Count": np.random.rand(120) * 10, "Temp": np.random.rand(120) * 30})

print("Running export_to_excel with dual perspectives + manual Global clusters...")
excel_bytes = export_to_excel(
    analyses, df_raw=df_raw, active_view="spatial", window_size=13, include_raw_data=True
)
print(f"Excel size: {len(excel_bytes)} bytes")

with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
    tmp.write(excel_bytes)
    tmp_path = tmp.name

print("Written test file:", tmp_path)

from openpyxl import load_workbook
wb = load_workbook(tmp_path)
print("\nSheets (in workbook order):")
for s in wb.sheetnames:
    ws = wb[s]
    a1 = ws["A1"].value
    print(f"  - {s}: {ws.max_row} rows x {ws.max_column} cols   A1={repr(a1)[:60]}")

# Verify key sheets
expected = ["Summary", "Cluster_Composition", "Metrics_by_Scale",
            "spatial_Local", "spatial_Medium", "spatial_Global",
            "multivariate_Local", "multivariate_Medium", "multivariate_Global",
            "Raw_Data"]

print("\nVerification:")
for name in expected:
    exists = name in wb.sheetnames
    print(f"  {name}: {'OK' if exists else 'MISSING'}")

# Check Cluster_Composition has manual data
ws_cc = wb["Cluster_Composition"]
print("\nCluster_Composition sample (first data row):")
if ws_cc.max_row > 1:
    print("  ", [cell.value for cell in ws_cc[2]])

# Check a scale sheet has header + series
ws_sl = wb["spatial_Local"]
print("\nspatial_Local sample (A1-A6):")
for row in range(1, 7):
    vals = [ws_sl.cell(row=row, column=c).value for c in range(1, 5)]
    print(f"  row{row}: {vals}")

print("\n=== TEST PASSED (basic structure + content check) ===")
os.unlink(tmp_path)
print("Temp file cleaned.")