import numpy as np
import pytest
from systemictau.gis import spatial_tau

def test_spatial_tau():
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        import libpysal
    except ImportError:
        pytest.skip("GeoPandas or libpysal not installed")
        
    # Create dummy GeoDataFrame
    points = [Point(0, 0), Point(0, 1), Point(1, 0), Point(1, 1)]
    gdf = gpd.GeoDataFrame({
        'geometry': points,
        't1': [1, 2, 3, 4],
        't2': [2, 3, 4, 1],
        't3': [3, 4, 1, 2]
    })
    
    res = spatial_tau(gdf, value_cols=['t1', 't2', 't3'], k_neighbors=2, window_size=2)
    assert 'spatial_tau' in res.columns
    assert 'hotspot_flag' in res.columns
    assert len(res) == 4
