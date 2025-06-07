"""
Main GUI application class for the weather helper.
Handles window setup and main widget initialization.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone
from src.gui.themes import apply_theme, FONTS, PADDING
from src.core.weather_api import fetch_weather_data
from src.core.locations import LOCATIONS
from src.core.evaluation import process_forecast, get_available_dates, get_top_locations_for_date, get_time_blocks_for_date
from src.utils.misc import get_rating_info, find_optimal_weather_block, format_human_date, get_weather_description


class WeatherHelperApp:
  def __init__(self):
    self.root = tk.Tk()
    self.root.title("Weather Helper")
    self.root.minsize(1100, 700)
    apply_theme(self.root)
    self.setup_window()
    self.main_frame = ttk.Frame(self.root, padding=PADDING['large'])
    self.main_frame.grid(row=0, column=0, sticky="nsew")
    self.root.columnconfigure(0, weight=1)
    self.root.rowconfigure(0, weight=1)
    self.main_frame.columnconfigure(0, weight=0)
    self.main_frame.columnconfigure(1, weight=1)
    self.main_frame.rowconfigure(3, weight=1)
    # Center the main title across the window
    self.title_label = ttk.Label(
        self.main_frame,
        text="Weather Helper",
        font=FONTS['title'],
        anchor="center",
        justify="center"
    )
    self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, PADDING['large']), sticky="ew")

    # Data storage
    self.all_location_processed = {}  # key: location_key, value: processed forecast dict
    self.selected_location_key = None
    self.selected_date = None

    # UI
    self.setup_selectors()
    self.setup_side_panel()
    self.setup_main_table()

    # Start data loading
    self.root.after(100, self.load_all_forecasts)

  def setup_window(self):
    """Configure the main window settings."""
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    window_width = 1200  # Increased width to better fit side panel
    window_height = 700
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

  def setup_selectors(self):
    selector_frame = ttk.Frame(self.main_frame)
    selector_frame.grid(row=1, column=1, sticky="ew", pady=(0, PADDING['medium']))

    # Location selector
    ttk.Label(selector_frame, text="Select Location:", font=FONTS['body']).grid(row=0, column=0, padx=(0, PADDING['medium']))
    self.location_var = tk.StringVar()
    self.location_dropdown = ttk.Combobox(
        selector_frame,
        textvariable=self.location_var,
        state="readonly",
        font=FONTS['body']
    )
    self.location_dropdown.grid(row=0, column=1, sticky="ew")
    self.location_dropdown.bind("<<ComboboxSelected>>", self.on_location_change)
    self.location_dropdown.configure(justify='left')

    # Date selector
    ttk.Label(selector_frame, text="Select Date:", font=FONTS['body']).grid(row=0, column=2, padx=(PADDING['large'], PADDING['medium']))
    self.date_var = tk.StringVar()
    self.date_dropdown = ttk.Combobox(
        selector_frame,
        textvariable=self.date_var,
        state="readonly",
        font=FONTS['body']
    )
    self.date_dropdown.grid(row=0, column=3, sticky="ew")
    self.date_dropdown.bind("<<ComboboxSelected>>", self.on_date_change)
    self.date_dropdown.configure(justify='left')

    selector_frame.columnconfigure(1, weight=1)
    selector_frame.columnconfigure(3, weight=1)

  def setup_side_panel(self):
    self.side_panel = ttk.Frame(self.main_frame, padding=PADDING['medium'])
    self.side_panel.grid(row=1, column=0, rowspan=5, sticky="nsew", padx=(0, PADDING['large']))
    self.side_panel.columnconfigure(0, weight=1)
    self.side_panel.rowconfigure(0, weight=0)  # Header row
    # Distribute location frames evenly
    for i in range(1, 6):
      self.side_panel.rowconfigure(i, weight=1)
    self.side_panel.config(width=320)
    heading_color = '#222'
    self.side_panel_title = ttk.Label(self.side_panel, text="Top 5 Locations", font=FONTS['heading'], anchor="w", justify="left", foreground=heading_color)
    self.side_panel_title.grid(row=0, column=0, sticky="w", pady=(6, PADDING['medium']))

    self.location_frames = []
    self.side_panel_entries = []

    for i in range(5):
      loc_frame = ttk.Frame(self.side_panel)
      # Use sticky="nsew" to expand vertically, and fill available space
      loc_frame.grid(row=i + 1, column=0, sticky="nsew", pady=(8 if i > 0 else 0, 4))
      self.location_frames.append(loc_frame)
      loc_frame.columnconfigure(0, weight=0)
      loc_frame.columnconfigure(1, weight=1)
      number_label = ttk.Label(loc_frame, text="", font=FONTS['body'], anchor="w", justify="left", foreground=heading_color)
      number_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
      name_score_label = ttk.Label(loc_frame, text="", font=FONTS['body'], anchor="w", justify="left", wraplength=300)
      name_score_label.grid(row=0, column=1, sticky="w", pady=(0, 2))
      best_label = ttk.Label(loc_frame, text="", font=FONTS['small'], anchor="w", justify="left", wraplength=300)
      best_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 0), padx=(24, 4))
      self.side_panel_entries.append((number_label, name_score_label, best_label))
    style = ttk.Style()
    style.configure('SidePanelName.TLabel', font=FONTS['body'])
    style.configure('SidePanelParam.TLabel', font=FONTS['small'])

  def setup_main_table(self):
    columns = ("Time", "Score", "Temperature", "Weather", "Wind", "Humidity")
    self.main_table = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=18)
    self.main_table.grid(row=3, column=1, sticky="nsew", pady=(PADDING['large'], 0), padx=(0, 20))
    col_widths = {
        "Time": 80,
        "Score": 110,
        "Temperature": 110,
        "Weather": 140,
        "Wind": 100,
        "Humidity": 100
    }
    for col in columns:
      self.main_table.heading(col, text=col)
      self.main_table.column(col, anchor="center", width=col_widths[col], minwidth=col_widths[col], stretch=False)
    self.main_frame.rowconfigure(3, weight=1)
    style = ttk.Style()
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def block_treeview_column_drag(event):
      if self.main_table.identify_region(event.x, event.y) == 'separator':
        return None
      return "break"
    self.main_table.bind('<Button-1>', block_treeview_column_drag, add='+')
    style.configure('Excellent.Treeview', foreground='#228B22')
    style.configure('VeryGood.Treeview', foreground='#388e3c')
    style.configure('Good.Treeview', foreground='#7e8c3b')
    style.configure('Fair.Treeview', foreground='#ffb300')
    style.configure('Poor.Treeview', foreground='#b22222')

  def load_all_forecasts(self):
    # Fetch and process forecasts for all locations
    for loc_key, loc in LOCATIONS.items():
      raw = fetch_weather_data(loc)
      if raw is not None:
        processed = process_forecast(raw, loc.name)
        if processed:
          self.all_location_processed[loc_key] = processed
    # Populate selectors
    self.populate_location_selector()

  def populate_location_selector(self):
    location_names = [loc.name for loc in LOCATIONS.values() if loc.key in self.all_location_processed]
    self.location_dropdown['values'] = location_names
    if location_names:
      self.location_var.set(location_names[0])
      self.on_location_change()

  def on_location_change(self, event=None):
    # Find the selected location key
    selected_name = self.location_var.get()
    for key, loc in LOCATIONS.items():
      if loc.name == selected_name:
        self.selected_location_key = key
        break
    # Try to keep the selected date if available
    previous_date = self.selected_date
    self.populate_date_selector()
    if previous_date and previous_date in self.date_map.values():
      # Set the date dropdown to the previous date
      for k, v in self.date_map.items():
        if v == previous_date:
          self.date_var.set(k)
          self.selected_date = previous_date
          break
      self.update_side_panel()
      self.update_main_table()

  def populate_date_selector(self):
    if not self.selected_location_key:
      self.date_dropdown['values'] = []
      self.date_map = {}
      return
    processed = self.all_location_processed.get(self.selected_location_key)
    if not processed:
      self.date_dropdown['values'] = []
      self.date_map = {}
      return
    available_dates = get_available_dates(processed)
    # Map human-readable string to date object
    self.date_map = {format_human_date(d): d for d in available_dates}
    date_strs = list(self.date_map.keys())
    self.date_dropdown['values'] = date_strs
    if date_strs:
      self.date_var.set(date_strs[0])
      self.on_date_change()

  def on_date_change(self, event=None):
    # Use the mapping to get the actual date
    selected_str = self.date_var.get()
    self.selected_date = self.date_map.get(selected_str)
    self.update_side_panel()
    self.update_main_table()

  def update_side_panel(self):
    if not self.selected_date:
      for number_label, name_score_label, best_label in self.side_panel_entries:
        number_label.config(text="")
        name_score_label.config(text="")
        best_label.config(text="")
      return
    date_obj = self.selected_date
    now = datetime.now(timezone.utc)
    top_locs = get_top_locations_for_date(self.all_location_processed, date_obj, top_n=5)
    for i, (number_label, name_score_label, best_label) in enumerate(self.side_panel_entries):
      if i < len(top_locs):
        loc = top_locs[i]
        score = loc.get('combined_score', 0)
        processed = self.all_location_processed.get(loc.get('location_key'))
        all_hours_for_day = []
        if processed and "daily_forecasts" in processed:
          all_hours_for_day = processed["daily_forecasts"].get(date_obj, [])
        filtered_hours = [h for h in all_hours_for_day if 8 <= h.time.hour <= 20 and (date_obj != now.date() or h.time.hour >= now.hour)]
        best_text = ""
        best_score = score
        best_rating = get_rating_info(score)
        limited_data = False
        if filtered_hours:
          weather_blocks_info = find_optimal_weather_block(filtered_hours)
          optimal_block = weather_blocks_info.get('optimal_block')
          if not optimal_block:
            best_hour = max(filtered_hours, key=lambda h: h.total_score)
            best_score = best_hour.total_score
            start_time = end_time = best_hour.time.strftime('%H:%M')
            duration = 1
            weather_type = get_weather_description(best_hour.symbol)
            best_text = f"Best: {start_time}-{end_time} ({weather_type} - {duration}h)\n"
            conditions = []
            if best_hour.temp is not None:
              conditions.append(f"Temperature: {best_hour.temp:.1f}°C")
            if best_hour.wind is not None:
              conditions.append(f"Wind: {best_hour.wind:.1f} m/s")
            if conditions:
              best_text += ", ".join(conditions)
          else:
            best_score = optimal_block["avg_score"]
            start_time = optimal_block["start"].strftime('%H:%M')
            end_time = optimal_block["end"].strftime('%H:%M')
            duration = optimal_block["duration"]
            weather_type = get_weather_description(optimal_block["weather"])
            best_text = f"Best: {start_time}-{end_time} ({weather_type} - {duration}h)\n"
            conditions = []
            if optimal_block["temp"] is not None:
              conditions.append(f"Temperature: {optimal_block['temp']:.1f}°C")
            if optimal_block["wind"] is not None:
              conditions.append(f"Wind: {optimal_block['wind']:.1f} m/s")
            if conditions:
              best_text += ", ".join(conditions)
          # If there are fewer than 3 hours, mark as limited data
          if len(filtered_hours) < 3:
            limited_data = True
          # If the best score is < 3, force the rating to 'Fair' or 'Poor'
          if best_score < 0:
            best_rating = 'Poor'
          elif best_score < 3:
            best_rating = 'Fair'
        else:
          best_text = "Best: No data"
          best_rating = get_rating_info(score)
        # Number label in heading color, rest in score color
        number_label.config(text=f"{i + 1}.", foreground=self.side_panel_title.cget('foreground'))
        name_score_label.config(text=f" {loc.get('location_name', 'Unknown')}: {best_rating} ({score:.1f})", foreground='#228B22' if best_rating ==
                                'Excellent' else '#388e3c' if best_rating == 'Very Good' else '#7e8c3b' if best_rating == 'Good' else '#ffb300' if best_rating == 'Fair' else '#b22222')
        if limited_data:
          best_label.config(text=best_text + "\n(Limited data)", foreground=name_score_label.cget('foreground'))
        else:
          best_label.config(text=best_text, foreground=name_score_label.cget('foreground'))
      else:
        number_label.config(text="")
        name_score_label.config(text="")
        best_label.config(text="")

  def update_main_table(self):
    for row in self.main_table.get_children():
      self.main_table.delete(row)
    if not (self.selected_location_key and self.selected_date):
      return
    date_obj = self.selected_date
    processed = self.all_location_processed.get(self.selected_location_key)
    if not processed:
      return
    time_blocks = get_time_blocks_for_date(processed, date_obj)
    now = datetime.now(timezone.utc)
    # Filter for only hours between 08:00 and 20:00 and only future hours
    if date_obj == now.date():
      time_blocks = [h for h in time_blocks if 8 <= h.hour <= 20 and h.hour >= now.hour]
    else:
      time_blocks = [h for h in time_blocks if 8 <= h.hour <= 20]
    for hour in time_blocks:
      time_str = hour.time.strftime('%H:%M')
      rating = get_rating_info(hour.total_score)
      score = f"{rating} ({hour.total_score:.1f})"
      temp = f"{hour.temp:.1f}°C" if hour.temp is not None else "N/A"
      weather = get_weather_description(hour.symbol) if hour.symbol else "N/A"
      wind = f"{hour.wind:.1f} m/s" if hour.wind is not None else "N/A"
      humidity = f"{hour.humidity:.0f}%" if hour.humidity is not None else "N/A"
      if hour.total_score >= 18:
        tag = 'Excellent'
      elif hour.total_score >= 13:
        tag = 'VeryGood'
      elif hour.total_score >= 8:
        tag = 'Good'
      elif hour.total_score >= 3:
        tag = 'Fair'
      else:
        tag = 'Poor'
      self.main_table.insert("", "end", values=(time_str, score, temp, weather, wind, humidity), tags=(tag,))
    self.main_table.tag_configure('Excellent', foreground='#228B22')
    self.main_table.tag_configure('VeryGood', foreground='#388e3c')
    self.main_table.tag_configure('Good', foreground='#7e8c3b')
    self.main_table.tag_configure('Fair', foreground='#ffb300')
    self.main_table.tag_configure('Poor', foreground='#b22222')

  def run(self):
    """Start the application main loop."""
    self.root.mainloop()


def main():
  app = WeatherHelperApp()
  app.run()


if __name__ == "__main__":
  main()
