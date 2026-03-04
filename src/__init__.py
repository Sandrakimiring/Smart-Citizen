"""Haki Sovereign AI Engine - SmartCitizen AI platform."""


def create_engine(force_rebuild=False):
    """Lazy factory — imports haki_engine only when called."""
    from .haki_engine import create_engine as _create
    return _create(force_rebuild)


def __getattr__(name):
    """Lazy attribute access for HakiSovereignEngine and HakiResponse."""
    if name in ("HakiSovereignEngine", "HakiResponse"):
        from .haki_engine import HakiSovereignEngine, HakiResponse
        return {"HakiSovereignEngine": HakiSovereignEngine, "HakiResponse": HakiResponse}[name]
    raise AttributeError(f"module 'src' has no attribute {name!r}")


__all__ = ["HakiSovereignEngine", "HakiResponse", "create_engine"]
