"""Optional nested-recd / excess³ integration tests."""

import numpy as np
import pytest

from systemictau import has_nested_recd, compute_nested_recd, __version__


def test_version_bump():
    assert __version__ == "3.1.0"


def test_has_nested_recd_bool():
    assert isinstance(has_nested_recd(), bool)


@pytest.mark.skipif(not has_nested_recd(), reason="nested-recd not installed")
def test_compute_nested_recd_shapes():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3)).cumsum(axis=0)
    # Provide tau_s so λ is not all zeros
    tau = rng.normal(size=200) * 0.1
    out = compute_nested_recd(X, tau_s=tau, m=3, theta3=0.10, window_tau=13)
    assert "excess3" in out
    assert "phi3" in out
    assert out["params"]["level3_primary"] == "excess3"
    assert out["params"]["alpha_syn"] == 0.6
    assert out["excess3"].shape == out["phi1"].shape


@pytest.mark.skipif(has_nested_recd(), reason="only when nested-recd missing")
def test_missing_nested_raises():
    with pytest.raises(ImportError, match="nested-recd"):
        compute_nested_recd(np.random.randn(50, 2))
