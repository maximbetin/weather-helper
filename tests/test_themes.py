"""
Tests for GUI themes and styling functionality.
"""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from src.gui.themes import BORDER, COLORS, FONTS, PADDING, apply_theme, get_rating_color


class TestColorsAndConstants:
  """Test that color constants and configurations are defined correctly."""

  def test_colors_defined(self):
    """Test that all expected colors are defined."""
    expected_colors = [
        'primary', 'primary_light', 'secondary', 'secondary_light',
        'accent', 'accent_light', 'success', 'success_light',
        'warning', 'warning_light', 'error', 'background', 'surface',
        'surface_secondary', 'border', 'text', 'text_secondary', 'text_muted',
        'excellent', 'very_good', 'good', 'fair', 'poor'
    ]

    for color in expected_colors:
      assert color in COLORS
      assert isinstance(COLORS[color], str)
      assert COLORS[color].startswith('#')
      assert len(COLORS[color]) == 7  # #RRGGBB format

  def test_fonts_defined(self):
    """Test that all expected fonts are defined."""
    expected_fonts = [
        'title', 'heading', 'subheading', 'body', 'body_bold',
        'small', 'small_bold', 'monospace'
    ]

    for font in expected_fonts:
      assert font in FONTS
      assert isinstance(FONTS[font], tuple)
      assert len(FONTS[font]) >= 2  # At least (family, size)

  def test_padding_defined(self):
    """Test that padding constants are defined."""
    expected_paddings = ['tiny', 'small', 'medium', 'large', 'xlarge']

    for padding in expected_paddings:
      assert padding in PADDING
      assert isinstance(PADDING[padding], int)
      assert PADDING[padding] >= 0

  def test_border_defined(self):
    """Test that border constants are defined."""
    expected_border_keys = ['width', 'color', 'focus_color']

    for key in expected_border_keys:
      assert key in BORDER


class TestGetRatingColor:
  """Test the get_rating_color function."""

  def test_rating_colors(self):
    """Test that rating colors return correct values."""
    assert get_rating_color("Excellent") == COLORS['excellent']
    assert get_rating_color("Very Good") == COLORS['very_good']
    assert get_rating_color("Good") == COLORS['good']
    assert get_rating_color("Fair") == COLORS['fair']
    assert get_rating_color("Poor") == COLORS['poor']

  def test_unknown_rating_returns_text_color(self):
    """Test that unknown ratings return the default text color."""
    assert get_rating_color("Unknown") == COLORS['text']
    assert get_rating_color("Invalid") == COLORS['text']
    assert get_rating_color("") == COLORS['text']


class TestApplyTheme:
  """Test the apply_theme function."""

  @pytest.fixture
  def mock_root(self):
    """Create a mock root window."""
    root = MagicMock()
    root.configure = MagicMock()
    return root

  @pytest.fixture
  def mock_style(self):
    """Create a mock ttk.Style object."""
    style = MagicMock()
    style.theme_use = MagicMock()
    style.configure = MagicMock()
    style.map = MagicMock()
    return style

  def test_apply_theme_basic_setup(self, mock_root, mock_style):
    """Test basic theme application setup."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Verify root configuration
      mock_root.configure.assert_called_once_with(background=COLORS['background'])

      # Verify style theme usage attempts
      assert mock_style.theme_use.call_count >= 1

  def test_apply_theme_vista_theme_success(self, mock_root, mock_style):
    """Test successful application of vista theme."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # First call should be 'vista'
      mock_style.theme_use.assert_any_call('vista')

  def test_apply_theme_vista_fallback_to_clam(self, mock_root, mock_style):
    """Test fallback to clam theme when vista fails."""
    # Make vista theme fail, clam succeed
    mock_style.theme_use.side_effect = [Exception("Vista not available"), None, None]

    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Should try vista, then clam
      assert mock_style.theme_use.call_count >= 2
      mock_style.theme_use.assert_any_call('vista')
      mock_style.theme_use.assert_any_call('clam')

  def test_apply_theme_fallback_to_default(self, mock_root, mock_style):
    """Test fallback to default theme when both vista and clam fail."""
    # Make both themes fail
    mock_style.theme_use.side_effect = [
        Exception("Vista not available"),
        Exception("Clam not available"),
        None
    ]

    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Should try vista, clam, then default
      assert mock_style.theme_use.call_count >= 3
      mock_style.theme_use.assert_any_call('default')

  def test_apply_theme_configures_styles(self, mock_root, mock_style):
    """Test that apply_theme configures all necessary styles."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Verify style.configure was called for major components
      configure_calls = [call[0][0] for call in mock_style.configure.call_args_list]

      expected_styles = [
          'TFrame', 'Card.TFrame', 'Sidebar.TFrame', 'TLabel', 'Sidebar.TLabel',
          'Title.TLabel', 'Heading.TLabel', 'Secondary.TLabel', 'TButton',
          'TCombobox', 'Custom.Treeview', 'Custom.Treeview.Heading',
          'Excellent.Custom.Treeview', 'VeryGood.Custom.Treeview',
          'Good.Custom.Treeview', 'Fair.Custom.Treeview', 'Poor.Custom.Treeview',
          'Status.TLabel'
      ]

      for expected_style in expected_styles:
        assert expected_style in configure_calls

  def test_apply_theme_maps_styles(self, mock_root, mock_style):
    """Test that apply_theme sets up style mappings."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Verify style.map was called for interactive components
      map_calls = [call[0][0] for call in mock_style.map.call_args_list]

      expected_mapped_styles = ['TButton', 'TCombobox']

      for expected_style in expected_mapped_styles:
        assert expected_style in map_calls

  def test_frame_configurations(self, mock_root, mock_style):
    """Test specific frame style configurations."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Find TFrame configure call
      tframe_call = None
      for call in mock_style.configure.call_args_list:
        if call[0][0] == 'TFrame':
          tframe_call = call[1]
          break

      assert tframe_call is not None
      assert tframe_call['background'] == COLORS['background']
      assert tframe_call['relief'] == 'flat'
      assert tframe_call['borderwidth'] == 0

  def test_label_configurations(self, mock_root, mock_style):
    """Test specific label style configurations."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Find TLabel configure call
      tlabel_call = None
      for call in mock_style.configure.call_args_list:
        if call[0][0] == 'TLabel':
          tlabel_call = call[1]
          break

      assert tlabel_call is not None
      assert tlabel_call['background'] == COLORS['background']
      assert tlabel_call['foreground'] == COLORS['text']
      assert tlabel_call['font'] == FONTS['body']

  def test_button_configurations(self, mock_root, mock_style):
    """Test specific button style configurations."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Find TButton configure call
      tbutton_call = None
      for call in mock_style.configure.call_args_list:
        if call[0][0] == 'TButton':
          tbutton_call = call[1]
          break

      assert tbutton_call is not None
      assert tbutton_call['background'] == COLORS['primary']
      assert tbutton_call['foreground'] == 'white'
      assert tbutton_call['font'] == FONTS['body']
      assert tbutton_call['relief'] == 'flat'

  def test_button_state_mappings(self, mock_root, mock_style):
    """Test button state mappings."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Find TButton map call
      tbutton_map = None
      for call in mock_style.map.call_args_list:
        if call[0][0] == 'TButton':
          tbutton_map = call[1]['background']
          break

      assert tbutton_map is not None
      # Should have mappings for active, pressed, disabled states
      state_mappings = dict(tbutton_map)
      assert 'active' in state_mappings
      assert 'pressed' in state_mappings
      assert 'disabled' in state_mappings

  def test_treeview_rating_styles(self, mock_root, mock_style):
    """Test that rating-specific Treeview styles are configured."""
    with patch('tkinter.ttk.Style', return_value=mock_style):
      apply_theme(mock_root)

      # Check that rating styles are configured
      configure_calls = [call[0][0] for call in mock_style.configure.call_args_list]

      rating_styles = [
          'Excellent.Custom.Treeview',
          'VeryGood.Custom.Treeview',
          'Good.Custom.Treeview',
          'Fair.Custom.Treeview',
          'Poor.Custom.Treeview'
      ]

      for rating_style in rating_styles:
        assert rating_style in configure_calls


class TestThemeIntegration:
  """Integration tests for theme functionality."""

  @pytest.fixture
  def root(self):
    """Create a real tkinter root for integration testing."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()

    # Verify root background was set
    assert root.cget('background') == COLORS['background']

  def test_theme_colors_valid(self):
    """Test that all theme colors are valid hex colors."""
    import re
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')

    for color_name, color_value in COLORS.items():
      assert hex_pattern.match(color_value), f"Invalid color format for {color_name}: {color_value}"
