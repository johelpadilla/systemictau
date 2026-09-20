"""Optional nested-recd / excess³ integration tests (systemictau 4.6+)."""

import numpy as np
import pytest

from systemictau import has_nested_recd, compute_nested_recd, __version__, run_full_analysis


def test_version_bump():
    assert __version__ == "4.6.1"


def test_has_nested_recd_bool():
    assert isinstance(has_nested_recd(), bool)


@pytest.mark.skipif(not has_nested_recd(), reason="nested-recd not installed")
def test_compute_nested_recd_shapes():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3)).cumsum(axis=0)
    tau = rng.normal(size=200) * 0.1
    out = compute_nested_recd(X, tau_s=tau, m=3, theta3=0.10, window_tau=13)
    assert "excess3" in out
    assert "phi3" in out
    assert out["params"]["level3_primary"] == "excess3"
    assert out["params"]["alpha_syn"] == 0.6
    assert out["excess3"].shape == out["phi1"].shape


@pytest.mark.skipif(not has_nested_recd(), reason="nested-recd not installed")
def test_run_full_analysis_nested_flag():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(150, 3)).cumsum(axis=0)
    res = run_full_analysis(X, window_size=13, compute_nested_recd=True)
    assert res.nested_recd_results is not None
    assert res.nested_recd_results.get("level3_primary") == "excess3"
    assert "mean_excess3" in res.nested_recd_results


@pytest.mark.skipif(has_nested_recd(), reason="only when nested-recd missing")
def test_missing_nested_raises():
    with pytest.raises(ImportError, match="nested-recd"):
        compute_nested_recd(np.random.randn(50, 2))
