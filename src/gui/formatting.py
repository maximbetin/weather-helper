"""
This module contains utility functions for formatting data for display in the GUI.
"""

import tkinter as tk

from src.application.presentation import (
    format_date,
    format_duration,
    format_percentage,
    format_precipitation,
    format_temperature,
    format_time,
    format_wind_speed,
)

TOOLTIP_OFFSET_X = 20
TOOLTIP_OFFSET_Y = 20
TOOLTIP_WRAP_LENGTH = 300
TOOLTIP_BORDER_WIDTH = 1


class ToolTip:
    """Simple tooltip implementation for GUI widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        """Show tooltip on mouse enter."""
        if self.tooltip_window:
            return
        x, y = self._tooltip_position()
        self.tooltip_window = self._create_tooltip_window(x, y)
        self._create_tooltip_label(self.tooltip_window).pack(ipadx=1)

    def _tooltip_position(self) -> tuple[int, int]:
        """Return screen coordinates for the tooltip."""
        bbox_x, bbox_y, _, _ = self._widget_bbox()
        x = self.widget.winfo_rootx() + bbox_x + TOOLTIP_OFFSET_X
        y = self.widget.winfo_rooty() + bbox_y + TOOLTIP_OFFSET_Y
        return x, y

    def _widget_bbox(self) -> tuple[int, int, int, int]:
        """Return the widget insertion bbox or a safe fallback."""
        if hasattr(self.widget, "bbox"):
            return self.widget.bbox("insert")
        return (0, 0, 0, 0)

    def _create_tooltip_window(self, x: int, y: int):
        """Create the tooltip toplevel window."""
        tooltip_window = tk.Toplevel(self.widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{x}+{y}")
        return tooltip_window

    def _create_tooltip_label(self, tooltip_window):
        """Create the label displayed inside the tooltip."""
        return tk.Label(
            tooltip_window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=TOOLTIP_BORDER_WIDTH,
            font=("Segoe UI", 8),
            wraplength=TOOLTIP_WRAP_LENGTH,
        )

    def on_leave(self, event=None):
        """Hide tooltip on mouse leave."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_tooltip(widget, text):
    """Add a tooltip to a widget."""
    return ToolTip(widget, text)


__all__ = [
    "ToolTip",
    "add_tooltip",
    "format_date",
    "format_duration",
    "format_percentage",
    "format_precipitation",
    "format_temperature",
    "format_time",
    "format_wind_speed",
]
