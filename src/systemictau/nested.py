"""
Nested ordinal RECD / continuous excess³ (Level-3).

Thin re-export of the canonical ``nested-recd`` package. Systemic Tau does
**not** reimplement Syn/Surp math here — install the optional extra:

    pip install "systemictau[nested]"
    # or
    pip install nested-recd>=0.2.0

Two RECD notions in this ecosystem
----------------------------------
1. **Gate RECD** (this package core): ``compute_recd_increments`` /
   ``accumulate_time`` from Systemic Tau (τ_s) and Feigenbaum gate.
2. **Nested ordinal RECD / excess³** (this module): Φ₁–Φ₃ on Bandt–Pompe
   symbols; continuous excess³ = 0.6·Syn + 0.4·Surp is the primary Level-3
   readout (methods DOI 10.5281/zenodo.21385937).

See also: https://github.com/johelpadilla/nested-recd
          https://github.com/johelpadilla/excess3
"""

from __future__ import annotations

_ERR = (
    "nested-recd is required for nested ordinal RECD / excess³. "
    'Install with: pip install "systemictau[nested]" '
    "or: pip install nested-recd>=0.2.0"
)


def _require_nested_recd():
    try:
        import nested_recd  # noqa: F401
        return nested_recd
    except ImportError as e:
        raise ImportError(_ERR) from e


def __getattr__(name: str):
    """Lazy re-export of nested_recd public API."""
    nr = _require_nested_recd()
    if name == "nested_recd":
        return nr
    if name == "HAS_NESTED_RECD":
        try:
            _require_nested_recd()
            return True
        except ImportError:
            return False
    if hasattr(nr, name):
        return getattr(nr, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def has_nested_recd() -> bool:
    """Return True if ``nested-recd`` is importable."""
    try:
        _require_nested_recd()
        return True
    except ImportError:
        return False


def compute_nested_recd(X, tau_s=None, **kwargs):
    """
    Convenience wrapper: nested ordinal RECD pipeline on multivariate series X.

    Parameters
    ----------
    X : array-like, shape (T, N)
    tau_s : optional 1d array
        Systemic Tau series for λ regime weights (recommended when available).
    **kwargs
        Forwarded to ``nested_recd.compute_recd_from_conjunctions``
        (m, d, theta3, window_tau, lam_override, stride, …).

    Returns
    -------
    dict
        Includes continuous ``excess3`` (primary Level-3), binary ``phi3``,
        Φ₁/Φ₂, and legacy ``delta_recd`` / ``T_recd``.
    """
    nr = _require_nested_recd()
    return nr.compute_recd_from_conjunctions(X, tau_s=tau_s, **kwargs)


__all__ = [
    "has_nested_recd",
    "compute_nested_recd",
    "HAS_NESTED_RECD",
]
