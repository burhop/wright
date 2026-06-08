from api.config import get_ui_theme


def test_get_ui_theme_default(monkeypatch):
    monkeypatch.delenv("UI_THEME", raising=False)
    assert get_ui_theme() == "dark"


def test_get_ui_theme_custom(monkeypatch):
    monkeypatch.setenv("UI_THEME", "light")
    assert get_ui_theme() == "light"
