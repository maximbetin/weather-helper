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
    'excellent': '#16a34a',      # Bright green - more distinct
    'very_good': '#0284c7',      # Sky blue - better contrast from excellent
    'good': '#7c3aed',           # Purple - distinct from others
    'fair': '#ea580c',           # Bright orange
    'poor': '#dc2626',           # Red
}

# Enhanced font configurations with better hierarchy
FONTS = {
    'title': ('Segoe UI', 28, 'bold'),
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
                  borderwidth=0)

  style.configure('Card.TFrame',
                  background=COLORS['surface'],
                  relief='solid',
                  borderwidth=1,
                  padding=2)

  style.configure('TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['body'])

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
                  fieldbackground=COLORS['surface'],
                  background=COLORS['surface'],
                  foreground=COLORS['text'],
                  font=FONTS['body'],
                  borderwidth=1,
                  relief='solid')

  style.map('TCombobox',
            fieldbackground=[('readonly', COLORS['surface']),
                             ('disabled', COLORS['surface_secondary'])],
            bordercolor=[('focus', COLORS['primary_light']),
                         ('!focus', COLORS['border'])])

  # Enhanced treeview styling
  style.configure('Treeview',
                  background=COLORS['surface'],
                  foreground=COLORS['text'],
                  font=FONTS['body'],
                  fieldbackground=COLORS['surface'],
                  borderwidth=1,
                  relief='solid')

  style.configure('Treeview.Heading',
                  background=COLORS['surface_secondary'],
                  foreground=COLORS['text'],
                  font=FONTS['body_bold'],
                  relief='flat',
                  borderwidth=1)

  style.map('Treeview.Heading',
            background=[('active', COLORS['primary_light']),
                        ('pressed', COLORS['primary'])])

  style.map('Treeview',
            background=[('selected', COLORS['primary_light']),
                        ('!selected', COLORS['surface'])],
            foreground=[('selected', 'white'),
                        ('!selected', COLORS['text'])])

  # Status bar styling
  style.configure('Status.TLabel',
                  background=COLORS['surface_secondary'],
                  foreground=COLORS['text_secondary'],
                  font=FONTS['small'],
                  padding=(PADDING['small'], PADDING['tiny']),
                  relief='sunken',
                  borderwidth=1)

  # Rating-specific tag styles for treeview
  style.configure('Excellent.Treeview', foreground=COLORS['excellent'])
  style.configure('VeryGood.Treeview', foreground=COLORS['very_good'])
  style.configure('Good.Treeview', foreground=COLORS['good'])
  style.configure('Fair.Treeview', foreground=COLORS['fair'])
  style.configure('Poor.Treeview', foreground=COLORS['poor'])


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
