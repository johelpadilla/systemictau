import pandas as pd
from systemictau.desktop.map_generator import SystemicTauMapGenerator
from systemictau.desktop.data import DataManager

data_mgr = DataManager()
data_mgr.is_panel = True
data_mgr.location_col = 'Location'
data_mgr.time_col = 'Date'

# Mock pivoted data (Macro-Systemic)
df = pd.DataFrame({
    'Date': pd.date_range('2020-01-01', periods=10),
    '1': [1,2,3,4,5,6,7,8,9,10],
    '2': [2,3,4,5,6,7,8,9,10,11],
    '3': [3,4,5,6,7,8,9,10,11,12]
})

macro_clusters = {
    'MacroCluster_SUM_3vars_v1': ['1', '2', '3']
}

results_df = pd.DataFrame([{
    'Location': 'MacroCluster_SUM_3vars_v1',
    'Tau_Max': 0.8,
    'Target': 'Tau_s',
    'p_value': 0.01,
    'Verdict': 'Pass',
    'Leading_Driver': '1'
}])

coords_df = pd.DataFrame({
    'Location': ['1', '2', '3'],
    'latitude': [10.0, 20.0, 30.0],
    'longitude': [-10.0, -20.0, -30.0]
})

try:
    SystemicTauMapGenerator.generate_map(
        results_df=results_df,
        coords_df=coords_df,
        location_col='Location',
        scale_markers=False,
        output_file='scratch/test_map_medium.html',
        macro_clusters=macro_clusters
    )
    print("Success")
except Exception as e:
    print(f"Error: {e}")
