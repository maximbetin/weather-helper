"""
Theme and styling configuration for the weather helper GUI.
"""

from tkinter import ttk

# Modern color scheme with better contrast and visual hierarchy
COLORS = {
    "primary": "#1e3a8a",  # Deep blue
    "primary_light": "#3b82f6",  # Bright blue
    "secondary": "#0f766e",  # Teal
    "secondary_light": "#14b8a6",  # Light teal
    "accent": "#dc2626",  # Red accent
    "accent_light": "#ef4444",  # Light red
    "success": "#059669",  # Green
    "success_light": "#10b981",  # Light green
    "warning": "#d97706",  # Orange
    "warning_light": "#f59e0b",  # Light orange
    "error": "#dc2626",  # Red
    "background": "#f8fafc",  # Very light gray
    "surface": "#ffffff",  # White
    "surface_secondary": "#f1f5f9",  # Light gray
    "border": "#e2e8f0",  # Light border
    "text": "#1e293b",  # Dark slate
    "text_secondary": "#64748b",  # Medium gray
    "text_muted": "#94a3b8",  # Light gray
    "excellent": "#15803d",  # Darker Green
    "very_good": "#65a30d",  # Darker Yellow-Green
    "good": "#ca8a04",  # Darker Yellow
    "fair": "#ea580c",  # Darker Orange
    "poor": "#b91c1c",  # Darker Red
}

# Enhanced font configurations with better hierarchy
FONTS = {
    "title": ("Segoe UI", 22, "bold"),  # Reduced from 28 to 22
    "heading": ("Segoe UI", 18, "bold"),
    "subheading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 11),
    "body_bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 9),
    "small_bold": ("Segoe UI", 9, "bold"),
    "monospace": ("Consolas", 10),
}

# Improved layout constants
PADDING = {
    "tiny": 2,
    "small": 6,
    "medium": 12,
    "large": 20,
    "xlarge": 32,
}

# Border radius simulation for modern look
BORDER = {
    "width": 1,
    "color": COLORS["border"],
    "focus_color": COLORS["primary_light"],
}

THEME_FALLBACKS = ("vista", "clam", "default")


def apply_theme(root):
    """Apply the modern theme to the root window and its widgets."""
    style = ttk.Style()
    _select_available_theme(style)
    root.configure(background=COLORS["background"])
    _configure_frame_styles(style)
    _configure_label_styles(style)
    _configure_button_styles(style)
    _configure_combobox_styles(style)
    _configure_toggle_styles(style)
    _configure_treeview_styles(style)
    _configure_rating_styles(style)
    _configure_author_style(style)


def _select_available_theme(style):
    """Select the first available ttk theme."""
    for theme_name in THEME_FALLBACKS:
        try:
            style.theme_use(theme_name)
            return
        except Exception:
            continue


def _configure_frame_styles(style):
    """Configure frame styles."""
    _configure_base_frame_style(style)
    _configure_card_frame_style(style)
    _configure_sidebar_frame_style(style)


def _configure_base_frame_style(style):
    """Configure the base frame style."""
    style.configure(
        "TFrame",
        background=COLORS["background"],
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
    )


def _configure_card_frame_style(style):
    """Configure card frame style."""
    style.configure(
        "Card.TFrame",
        background=COLORS["background"],
        relief="flat",
        borderwidth=0,
        padding=2,
    )


def _configure_sidebar_frame_style(style):
    """Configure sidebar frame style."""
    style.configure(
        "Sidebar.TFrame",
        background=COLORS["background"],
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
    )


def _configure_label_styles(style):
    """Configure standard label styles."""
    _configure_base_label_style(style)
    _configure_sidebar_label_style(style)
    _configure_title_label_style(style)
    _configure_heading_label_style(style)
    _configure_secondary_label_style(style)
    _configure_status_label_style(style)


def _configure_base_label_style(style):
    """Configure the base label style."""
    style.configure(
        "TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["body"],
    )


def _configure_sidebar_label_style(style):
    """Configure sidebar label style."""
    style.configure(
        "Sidebar.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["body"],
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
    )


def _configure_title_label_style(style):
    """Configure title label style."""
    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["primary"],
        font=FONTS["title"],
    )


def _configure_heading_label_style(style):
    """Configure heading label style."""
    style.configure(
        "Heading.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["heading"],
    )


def _configure_secondary_label_style(style):
    """Configure secondary label style."""
    style.configure(
        "Secondary.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text_secondary"],
        font=FONTS["small"],
    )


def _configure_status_label_style(style):
    """Configure status label style."""
    style.configure(
        "Status.TLabel",
        background=COLORS["background"],
        foreground=COLORS["accent"],
        font=FONTS["body_bold"],
    )


def _configure_button_styles(style):
    """Configure button styles."""
    style.configure(
        "TButton",
        background=COLORS["primary"],
        foreground="white",
        font=FONTS["body"],
        padding=(PADDING["medium"], PADDING["small"]),
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[
            ("active", COLORS["primary_light"]),
            ("pressed", COLORS["primary"]),
            ("disabled", COLORS["text_muted"]),
        ],
    )


def _configure_combobox_styles(style):
    """Configure combobox styles."""
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["background"],
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["body"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", COLORS["background"]),
            ("disabled", COLORS["background"]),
        ],
        bordercolor=[("focus", COLORS["primary_light"]), ("!focus", COLORS["border"])],
    )


def _configure_toggle_styles(style):
    """Configure checkbox styles."""
    style.configure(
        "Toggle.TCheckbutton",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["body"],
        padding=(PADDING["small"], PADDING["tiny"]),
    )
    style.map(
        "Toggle.TCheckbutton",
        background=[
            ("active", COLORS["background"]),
            ("selected", COLORS["background"]),
        ],
        foreground=[("active", COLORS["primary"]), ("selected", COLORS["primary"])],
    )


def _configure_treeview_styles(style):
    """Configure table styles."""
    style.configure(
        "Custom.Treeview",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["surface"],
        font=FONTS["body"],
    )
    style.configure(
        "Custom.Treeview.Heading",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=FONTS["body_bold"],
        relief="flat",
        borderwidth=1,
    )


def _configure_rating_styles(style):
    """Configure rating-specific row styles."""
    style.configure("Excellent.Custom.Treeview", foreground=COLORS["excellent"])
    style.configure("VeryGood.Custom.Treeview", foreground=COLORS["very_good"])
    style.configure("Good.Custom.Treeview", foreground=COLORS["good"])
    style.configure("Fair.Custom.Treeview", foreground=COLORS["fair"])
    style.configure("Poor.Custom.Treeview", foreground=COLORS["poor"])


def _configure_author_style(style):
    """Configure author attribution style."""
    style.configure(
        "Author.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text_muted"],
        font=FONTS["small"],
    )


def get_rating_color(rating: str) -> str:
    """Get the color for a specific rating."""
    rating_colors = {
        "Excellent": COLORS["excellent"],
        "Very Good": COLORS["very_good"],
        "Good": COLORS["good"],
        "Fair": COLORS["fair"],
        "Poor": COLORS["poor"],
    }
    return rating_colors.get(rating, COLORS["text"])
