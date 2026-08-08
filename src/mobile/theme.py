"""Colour and type scale for the mobile screen.

Keeping these in one place is what stops the screen drifting into a dozen
slightly different greys and font sizes, and it makes the dark palette a
single switch rather than a per-widget decision.
"""

from dataclasses import dataclass

from src.application.presentation import (
    get_palette,
    get_rating_background,
    get_rating_color,
)

# Type scale. Nothing carrying data is allowed below BODY, so the screen stays
# readable at arm's length on a phone.
TITLE_SIZE = 20
HEADLINE_SIZE = 28
SUBTITLE_SIZE = 17
BODY_SIZE = 15
LABEL_SIZE = 13

SPACING = 12
CARD_RADIUS = 16
MIN_TOUCH_TARGET = 48


@dataclass(frozen=True)
class Palette:
    """Resolved colours for one brightness."""

    dark: bool

    def __getitem__(self, key: str) -> str:
        return get_palette(self.dark)[key]

    @property
    def background(self) -> str:
        return self["background"]

    @property
    def surface(self) -> str:
        return self["surface"]

    @property
    def text(self) -> str:
        return self["text"]

    @property
    def text_secondary(self) -> str:
        return self["text_secondary"]

    @property
    def primary(self) -> str:
        return self["primary"]

    @property
    def border(self) -> str:
        return self["border"]

    def rating(self, rating: str) -> str:
        """Return the foreground colour for a rating."""
        return get_rating_color(rating, self.dark)

    def rating_background(self, rating: str) -> str:
        """Return the surface tint for a rating."""
        return get_rating_background(rating, self.dark)
