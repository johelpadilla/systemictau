import pytest
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
    # Check metadata
    assert data["metadata"]["window_size"] == 3
