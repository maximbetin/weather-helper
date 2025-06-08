import pytest
import tkinter as tk
from src.gui.themes import apply_theme


def test_apply_theme_runs():
  root = tk.Tk()
  try:
    apply_theme(root)
  finally:
    root.destroy()
