import pytest
import numpy as np
from fastapi.testclient import TestClient

try:
    from systemictau.platform.api.main import app
    client = TestClient(app)
    has_fastapi = True
except ImportError:
    has_fastapi = False

@pytest.mark.skipif(not has_fastapi, reason="FastAPI not installed")
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

@pytest.mark.skipif(not has_fastapi, reason="FastAPI not installed")
def test_compute_tau_endpoint():
    # Simple dataset 4x2
    payload = {
        "data": [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0]
        ],
        "window_size": 3
    }
    response = client.post("/compute/tau", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "taus_global" in data
    assert "metadata" in data
    assert len(data["taus_global"]) == 4
    # First 2 should be None because window is 3
    assert data["taus_global"][0] is None
    assert data["taus_global"][1] is None
    assert data["metadata"]["window_size"] == 3

@pytest.mark.skipif(not has_fastapi, reason="FastAPI not installed")
def test_layers_endpoints():
    payload = {
        "taus_global": [np.nan, 0.5, 0.6, 0.7, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        "taus_per_module": [[np.nan, np.nan], [0.5, 0.5], [0.6, 0.6], [0.7, 0.7], 
                            [0.1, 0.1], [0.1, 0.1], [0.1, 0.1], [0.1, 0.1], 
                            [0.1, 0.1], [0.1, 0.1], [0.1, 0.1], [0.1, 0.1]],
        "theta_A": 0.04,
        "theta_M": 0.0,
        "D_min": 2
    }
    
    res1 = client.post("/layers/joint_episodes", json=payload)
    assert res1.status_code == 200
    assert "episodes" in res1.json()
    
    res2 = client.post("/detect/ascent", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert "t_frob" in data2
    assert "t_ks" in data2
    assert "t_star" in data2
