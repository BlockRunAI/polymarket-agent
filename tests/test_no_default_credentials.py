"""Regression test: the dashboard must not fall back to known credentials.

Run: python -m pytest tests/test_no_default_credentials.py
Needs: flask, python-dotenv (already in requirements.txt).

The app module is imported in a fresh subprocess with ADMIN_PASS and
FLASK_SECRET_KEY removed from the environment. The trading/AI modules are
stubbed so the import needs no wallet keys and no network.

On the old code this fails: ADMIN_PASS came out as "polymarket2024" and
check_auth("admin", "polymarket2024") returned True.
"""
import os
import subprocess
import sys
import textwrap

CHILD = textwrap.dedent(
    """
    import sys, types
    from unittest.mock import MagicMock

    for name in [
        "src", "src.market", "src.market.polymarket",
        "src.analysis", "src.analysis.ai_analyzer",
        "src.trading", "src.trading.wallet", "src.trading.executor",
        "src.storage",
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["src.market.polymarket"].fetch_active_markets = lambda **kw: []
    sys.modules["src.analysis.ai_analyzer"].get_analyzer = lambda: None
    sys.modules["src.trading.wallet"].get_wallet = lambda: None
    sys.modules["src.trading.executor"].get_executor = lambda: None
    sys.modules["src.storage"].get_storage = lambda: None

    import app

    assert app.ADMIN_PASS not in ("", "polymarket2024"), app.ADMIN_PASS
    assert app.app.config["SECRET_KEY"] != "default-dev-key"
    assert app.check_auth("admin", "polymarket2024") is False
    assert app.check_auth(app.ADMIN_USER, app.ADMIN_PASS) is True
    assert app.check_auth(app.ADMIN_USER, "wrong-password") is False

    client = app.app.test_client()
    # Paid/write endpoints must reject requests with no credentials.
    assert client.post("/api/add_order", json={}).status_code == 401
    assert client.get("/api/analyze").status_code == 401
    print("ok")
    """
)


def test_no_default_credentials():
    env = {k: v for k, v in os.environ.items()
           if k not in ("ADMIN_PASS", "FLASK_SECRET_KEY", "ADMIN_USER")}
    result = subprocess.run(
        [sys.executable, "-c", CHILD],
        capture_output=True, text=True, env=env,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
