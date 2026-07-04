import pandas as pd
from systemictau.desktop.map_generator import SystemicTauMapGenerator

# Mock results
results_df = pd.DataFrame({
    'Location': ['1', 'MacroCluster_SUM_2vars'],
    'Tau_Max': [0.5, 0.8],
    'Target': ['Tau_s', 'Tau_s'],
    'p_value': [0.01, 0.05],
    'Verdict': ['Pass', 'Pass'],
    'Leading Driver': ['A', 'B']
})

# Mock coords
coords_df = pd.DataFrame({
    'Location': ['1', '2', '3'],
    'latitude': [10.0, 20.0, 30.0],
    'longitude': [-10.0, -20.0, -30.0]
})

# Mock macro clusters
macro_clusters = {
    'MacroCluster_SUM_2vars': ['2', '3']
}

try:
    SystemicTauMapGenerator.generate_map(
        results_df=results_df,
        coords_df=coords_df,
        location_col='Location',
        scale_markers=False,
        output_file='scratch/test_map.html',
        macro_clusters=macro_clusters
    )
    print("Map generated successfully. Check scratch/test_map.html")
except Exception as e:
    import traceback
    traceback.print_exc()
