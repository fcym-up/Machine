"""Voice module tests — token endpoint and instructions builder."""
from app.api.v1.voice import router, _build_instructions


def test_router_has_token_endpoint():
    paths = [r.path for r in router.routes]
    assert "/token" in paths


def test_build_instructions_runs():
    r = _build_instructions()
    assert len(r) > 50 and "Machine" in r


def test_main_imports():
    from app.main import app
    assert app.title == "Project Machine"
