import pytest

from src.mobile import app


def test_missing_flet_has_actionable_install_message(monkeypatch):
    def missing_flet(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(app, "import_module", missing_flet)

    with pytest.raises(RuntimeError, match=r"pip install .*\[mobile\]"):
        app._load_flet()


@pytest.mark.parametrize(
    ("rating", "expected"),
    [
        ("Excellent", "#15803d"),
        ("Very Good", "#65a30d"),
        ("Good", "#ca8a04"),
        ("Fair", "#ea580c"),
        ("Poor", "#b91c1c"),
    ],
)
def test_mobile_rating_colors_match_windows_palette(rating, expected):
    assert app.rating_color(rating) == expected
    assert app.rating_background(rating) != app.SURFACE_COLOR
