"""
Theme and styling configuration for the weather helper GUI.
"""

from tkinter import ttk

# Modern color scheme with better contrast and visual hierarchy
COLORS = {
    'primary': '#1e3a8a',        # Deep blue
    'primary_light': '#3b82f6',  # Bright blue
    'secondary': '#0f766e',      # Teal
    'secondary_light': '#14b8a6',  # Light teal
    'accent': '#dc2626',         # Red accent
    'accent_light': '#ef4444',   # Light red
    'success': '#059669',        # Green
    'success_light': '#10b981',  # Light green
    'warning': '#d97706',        # Orange
    'warning_light': '#f59e0b',  # Light orange
    'error': '#dc2626',          # Red
    'background': '#f8fafc',     # Very light gray
    'surface': '#ffffff',        # White
    'surface_secondary': '#f1f5f9',  # Light gray
    'border': '#e2e8f0',         # Light border
    'text': '#1e293b',           # Dark slate
    'text_secondary': '#64748b',  # Medium gray
    'text_muted': '#94a3b8',     # Light gray
    'excellent': '#15803d',      # Darker Green
    'very_good': '#65a30d',      # Darker Yellow-Green
    'good': '#ca8a04',           # Darker Yellow
    'fair': '#ea580c',           # Darker Orange
    'poor': '#b91c1c',           # Darker Red
}

# Enhanced font configurations with better hierarchy
FONTS = {
    'title': ('Segoe UI', 22, 'bold'),  # Reduced from 28 to 22
    'heading': ('Segoe UI', 18, 'bold'),
    'subheading': ('Segoe UI', 14, 'bold'),
    'body': ('Segoe UI', 11),
    'body_bold': ('Segoe UI', 11, 'bold'),
    'small': ('Segoe UI', 9),
    'small_bold': ('Segoe UI', 9, 'bold'),
    'monospace': ('Consolas', 10),
}

# Improved layout constants
PADDING = {
    'tiny': 2,
    'small': 6,
    'medium': 12,
    'large': 20,
    'xlarge': 32,
}

# Border radius simulation for modern look
BORDER = {
    'width': 1,
    'color': COLORS['border'],
    'focus_color': COLORS['primary_light'],
}


def apply_theme(root):
  """Apply the modern theme to the root window and its widgets."""
  style = ttk.Style()

  # Use a modern theme as base
  try:
    style.theme_use('vista')  # Windows modern theme
  except:
    try:
      style.theme_use('clam')  # Cross-platform modern theme
    except:
      style.theme_use('default')

  # Configure root window
  root.configure(background=COLORS['background'])

  # Configure ttk styles with modern appearance
  style.configure('TFrame',
                  background=COLORS['background'],
                  relief='flat',
                  borderwidth=0,
                  highlightthickness=0)

  style.configure('Card.TFrame',
                  background=COLORS['background'],
                  relief='flat',
                  borderwidth=0,
                  padding=2)

  # Sidebar content frame with unified background
  style.configure('Sidebar.TFrame',
                  background=COLORS['background'],
                  relief='flat',
                  borderwidth=0,
                  highlightthickness=0)

  style.configure('TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['body'])

  # Sidebar label styling for unified appearance
  style.configure('Sidebar.TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['body'],
                  relief='flat',
                  borderwidth=0,
                  highlightthickness=0)

  style.configure('Title.TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['primary'],
                  font=FONTS['title'])

  style.configure('Heading.TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['heading'])

  style.configure('Secondary.TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text_secondary'],
                  font=FONTS['small'])

  # Enhanced button styling
  style.configure('TButton',
                  background=COLORS['primary'],
                  foreground='white',
                  font=FONTS['body'],
                  padding=(PADDING['medium'], PADDING['small']),
                  relief='flat',
                  borderwidth=0)

  style.map('TButton',
            background=[('active', COLORS['primary_light']),
                        ('pressed', COLORS['primary']),
                        ('disabled', COLORS['text_muted'])])

  # Modern combobox styling
  style.configure('TCombobox',
                  fieldbackground=COLORS['background'],
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['body'],
                  borderwidth=1,
                  relief='solid')

  style.map('TCombobox',
            fieldbackground=[('readonly', COLORS['background']),
                             ('disabled', COLORS['background'])],
            bordercolor=[('focus', COLORS['primary_light']),
                         ('!focus', COLORS['border'])])

  # Create a custom style for the Treeview
  style.configure('Custom.Treeview',
                  background=COLORS['surface'],
                  foreground=COLORS['text'],
                  fieldbackground=COLORS['surface'],
                  font=FONTS['body'])

  style.configure('Custom.Treeview.Heading',
                  background=COLORS['surface'],
                  foreground=COLORS['text'],
                  font=FONTS['body_bold'],
                  relief='flat',
                  borderwidth=1)

  # Configure rating-specific styles
  style.configure('Excellent.Custom.Treeview', foreground=COLORS['excellent'])
  style.configure('VeryGood.Custom.Treeview', foreground=COLORS['very_good'])
  style.configure('Good.Custom.Treeview', foreground=COLORS['good'])
  style.configure('Fair.Custom.Treeview', foreground=COLORS['fair'])
  style.configure('Poor.Custom.Treeview', foreground=COLORS['poor'])

  # Status bar styling
  style.configure('Status.TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text_secondary'],
                  font=FONTS['small'],
                  padding=(PADDING['small'], PADDING['tiny']),
                  relief='flat',
                  borderwidth=0)


def get_rating_color(rating: str) -> str:
  """Get the color for a specific rating."""
  rating_colors = {
      'Excellent': COLORS['excellent'],
      'Very Good': COLORS['very_good'],
      'Good': COLORS['good'],
      'Fair': COLORS['fair'],
      'Poor': COLORS['poor'],
  }
  return rating_colors.get(rating, COLORS['text'])
