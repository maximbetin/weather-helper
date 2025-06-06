"""
Theme and styling configuration for the weather helper GUI.
"""

from tkinter import ttk

# Color scheme
COLORS = {
    'primary': '#2c3e50',      # Dark blue-gray
    'secondary': '#3498db',    # Bright blue
    'accent': '#e74c3c',       # Red
    'background': '#ecf0f1',   # Light gray
    'text': '#2c3e50',         # Dark blue-gray
    'text_light': '#7f8c8d',   # Medium gray
    'success': '#2ecc71',      # Green
    'warning': '#f1c40f',      # Yellow
    'error': '#e74c3c',        # Red
}

# Font configurations
FONTS = {
    'title': ('Helvetica', 24, 'bold'),
    'heading': ('Helvetica', 18, 'bold'),
    'subheading': ('Helvetica', 14, 'bold'),
    'body': ('Helvetica', 12),
    'small': ('Helvetica', 10),
}

# Layout constants
PADDING = {
    'small': 5,
    'medium': 10,
    'large': 20,
}

# Widget styles
STYLES = {
    'button': {
        'padding': (10, 5),
        'font': FONTS['body'],
    },
    'label': {
        'font': FONTS['body'],
        'padding': PADDING['small'],
    },
    'entry': {
        'font': FONTS['body'],
        'padding': PADDING['small'],
    },
}


def apply_theme(root):
  """Apply the theme to the root window and its widgets."""
  style = ttk.Style()

  # Configure ttk styles
  style.configure('TFrame', background=COLORS['background'])
  style.configure('TLabel',
                  background=COLORS['background'],
                  foreground=COLORS['text'],
                  font=FONTS['body'])
  style.configure('TButton',
                  background=COLORS['secondary'],
                  foreground='white',
                  font=FONTS['body'],
                  padding=STYLES['button']['padding'])
  style.configure('TEntry',
                  fieldbackground='white',
                  font=FONTS['body'],
                  padding=STYLES['entry']['padding'])

  # Configure the root window
  root.configure(background=COLORS['background'])
