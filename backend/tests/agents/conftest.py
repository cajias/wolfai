import pytest


def pytest_collection_modifyitems(config, items):
    """Skip agent tests that require SWI-Prolog if it's not available."""
    try:
        from pyswip import Prolog  # noqa: F401
        swipl_available = True
    except Exception:
        swipl_available = False

    if not swipl_available:
        skip_swipl = pytest.mark.skip(reason="SWI-Prolog not available")
        for item in items:
            # Skip all agent tests if Prolog is not available, since PrologAgent is the main agent
            if "test_prolog" in str(item.fspath):
                item.add_marker(skip_swipl)
