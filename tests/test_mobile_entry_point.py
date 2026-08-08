import pytest

from src.mobile import app
from src.mobile.theme import Palette


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
    light = Palette(dark=False)

    assert light.rating(rating) == expected
    assert light.rating_background(rating) != light.surface


@pytest.mark.parametrize("rating", ["Excellent", "Very Good", "Good", "Fair", "Poor"])
def test_every_rating_stays_distinguishable_in_dark_mode(rating):
    dark = Palette(dark=True)

    assert dark.rating(rating) != dark.text
    assert dark.rating_background(rating) != dark.surface
    assert dark.rating(rating) != Palette(dark=False).rating(rating)
