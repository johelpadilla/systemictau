import numpy as np
import pytest
from systemictau.data import preprocess, from_dataframe

def test_preprocess_linear():
    """Test NaN linear interpolation."""
    X = np.array([
        [1.0, 2.0],
        [np.nan, 3.0],
        [3.0, np.nan],
        [4.0, 5.0]
    ])
    
    X_clean = preprocess(X, method='linear')
    assert X_clean[1, 0] == 2.0
    assert X_clean[2, 1] == 4.0
    
def test_from_dataframe():
    """Test from_dataframe integration."""
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({
        'time': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        'A': np.random.rand(14),
        'B': np.random.rand(14)
    })
    
    res = from_dataframe(df, time_col='time', window_size=5)
    assert res.taus_global.shape == (14,)
    assert not np.isnan(res.taus_global[-1])
