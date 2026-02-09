"""
Main GUI application class for the weather helper.
Handles window setup and main widget initialization.
"""

import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import date, datetime, timezone
from tkinter import ttk
from typing import Any, Dict, List

from src.core.config import (
    DAYLIGHT_END_HOUR,
    DAYLIGHT_START_HOUR,
    get_timezone,
)
from src.core.evaluation import (
    _find_optimal_consistent_block,
    get_available_dates,
    get_time_blocks_for_date,
    get_top_locations_for_date,
    process_forecast,
)
from src.core.scoring import get_rating_info, normalize_score
from src.core.locations import LOCATIONS, LOCATION_GROUPS
from src.core.weather_api import fetch_weather_data
from src.gui.formatting import add_tooltip, format_date
from src.gui.themes import COLORS, FONTS, PADDING, apply_theme, get_rating_color


class WeatherHelperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Weather Helper")
        self.root.minsize(1200, 750)
        apply_theme(self.root)

        # Initialize data and UI state
        self._init_data_storage()
        self._setup_ui()

        # Start loading data asynchronously
        self.root.after(100, self._start_data_loading)

    def _init_data_storage(self):
        """Initialize data storage attributes."""
        self.all_location_processed: Dict[str, Any] = {}
        self.selected_location_key: str = ""
        self.selected_date = None
        self.date_map: Dict[str, date] = {}
        self.loading_errors: Dict[str, str] = {}
        self.show_scores = tk.BooleanVar(value=False)
        self.loaded_locations: set = set()
        self.load_generation: int = 0

        # Default to Asturias
        self.current_locations = LOCATIONS
        self.total_locations: int = len(self.current_locations)

    def _setup_ui(self):
        """Setup the main UI layout and widgets."""
        self._setup_window()
        self._create_main_layout()
        self._setup_title_area()
        self._setup_status_bar()
        self._setup_main_table()  # Create main content container first
        self._setup_selectors()  # Then add selectors to it
        self._setup_side_panel()  # Finally setup side panel

    def _setup_window(self):
        """Configure the main window settings."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1400
        window_height = 1100

        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Disable resizing to prevent window from becoming too small
        self.root.resizable(False, False)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _create_main_layout(self):
        """Create the main layout structure."""
        self.main_frame = ttk.Frame(self.root, padding=PADDING["large"])
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=0, minsize=360)  # Side panel
        self.main_frame.columnconfigure(1, weight=1)  # Main content

        # Row configuration
        self.main_frame.rowconfigure(0, weight=0)  # Status bar (top)
        self.main_frame.rowconfigure(1, weight=0)  # Title
        self.main_frame.rowconfigure(2, weight=1)  # Content area

    def _setup_title_area(self):
        """Setup the title area."""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, PADDING["small"])
        )
        title_frame.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(
            title_frame, text="Weather Helper", style="Title.TLabel", anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

        self.subtitle_label = ttk.Label(
            title_frame,
            text="Loading weather data...",
            style="Secondary.TLabel",
            anchor="center",
        )
        self.subtitle_label.grid(
            row=1, column=0, sticky="ew", pady=(PADDING["small"], 0)
        )

    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, PADDING["medium"])
        )
        self.status_frame.columnconfigure(1, weight=1)
        self.status_frame.columnconfigure(2, weight=0)  # For author label

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode="determinate",
            variable=self.progress_var,
            length=200,
        )
        self.progress_bar.grid(row=0, column=0, padx=(0, PADDING["medium"]))

        self.status_label = ttk.Label(
            self.status_frame, text="Initializing...", style="Status.TLabel", anchor="w"
        )
        self.status_label.grid(row=0, column=1, sticky="ew")

        # Add subtle author attribution to status bar
        current_year = datetime.now().year
        self.author_label = ttk.Label(
            self.status_frame,
            text=f"© {current_year} Maxim BK",
            style="Author.TLabel",
            anchor="e",
        )
        self.author_label.grid(row=0, column=2, sticky="e", padx=(PADDING["medium"], 0))

    def _setup_selectors(self):
        """Setup location and date selectors."""
        selector_frame = ttk.Frame(
            self.main_content_container, style="Card.TFrame", padding=PADDING["medium"]
        )
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, PADDING["small"]))

        # Configure columns: Region, Location, Date
        selector_frame.columnconfigure(1, weight=1)
        selector_frame.columnconfigure(3, weight=1)
        selector_frame.columnconfigure(5, weight=1)

        # Region Selector
        ttk.Label(selector_frame, text="Region:", font=FONTS["body_bold"]).grid(
            row=0, column=0, padx=(0, PADDING["small"]), sticky="w"
        )

        self.group_var = tk.StringVar(value="Asturias")
        self.group_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.group_var,
            state="readonly",
            font=FONTS["body"],
            width=15,
            values=list(LOCATION_GROUPS.keys())
        )
        self.group_dropdown.grid(
            row=0, column=1, sticky="ew", padx=(0, PADDING["large"])
        )
        self.group_dropdown.bind("<<ComboboxSelected>>", self.on_group_change)
        add_tooltip(self.group_dropdown, "Select a region to load locations from")

        # Location selector
        ttk.Label(selector_frame, text="Location:", font=FONTS["body_bold"]).grid(
            row=0, column=2, padx=(0, PADDING["small"]), sticky="w"
        )

        self.location_var = tk.StringVar()
        self.location_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.location_var,
            state="readonly",
            font=FONTS["body"],
            width=25,
        )
        self.location_dropdown.grid(
            row=0, column=3, sticky="ew", padx=(0, PADDING["large"])
        )
        self.location_dropdown.bind("<<ComboboxSelected>>", self.on_location_change)
        add_tooltip(
            self.location_dropdown, "Select a location to view weather forecast"
        )

        # Date selector
        ttk.Label(selector_frame, text="Date:", font=FONTS["body_bold"]).grid(
            row=0, column=4, padx=(0, PADDING["small"]), sticky="w"
        )

        self.date_var = tk.StringVar()
        self.date_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.date_var,
            state="readonly",
            font=FONTS["body"],
            width=20,
        )
        self.date_dropdown.grid(row=0, column=5, sticky="ew")
        self.date_dropdown.bind("<<ComboboxSelected>>", self.on_date_change)
        add_tooltip(self.date_dropdown, "Select a date to view hourly weather data")

        # Score visibility toggle
        self.score_toggle = ttk.Checkbutton(
            selector_frame,
            text="Show scoring values",
            variable=self.show_scores,
            command=self._on_score_toggle_change,
            style="Toggle.TCheckbutton",
        )
        self.score_toggle.grid(
            row=1, column=0, columnspan=6, sticky="w", pady=(PADDING["small"], 0)
        )
        add_tooltip(
            self.score_toggle,
            "Toggle to show/hide the scoring values for each weather parameter",
        )

    def _on_score_toggle_change(self):
        """Handle the score visibility toggle."""
        self._update_displays()

    def _setup_side_panel(self):
        """Setup the side panel."""
        self.side_panel = ttk.Frame(
            self.main_frame, style="Sidebar.TFrame", padding=PADDING["small"]
        )
        self.side_panel.grid(row=2, column=0, sticky="nsew", padx=(0, PADDING["small"]))
        self.side_panel.columnconfigure(0, weight=1)

        title_label = ttk.Label(
            self.side_panel,
            text="Top 10 Locations",
            style="Heading.TLabel",
            anchor="center",
        )
        title_label.grid(row=0, column=0, sticky="ew", pady=(0, PADDING["small"]))

        self.location_frames = []
        self.side_panel_entries = []

        for i in range(10):
            loc_frame = ttk.Frame(
                self.side_panel, padding=(PADDING["small"], PADDING["small"])
            )
            loc_frame.grid(row=i + 1, column=0, sticky="ew", pady=PADDING["tiny"])
            loc_frame.columnconfigure(1, weight=1)
            loc_frame.rowconfigure(0, weight=0)
            loc_frame.rowconfigure(1, weight=0)
            loc_frame.rowconfigure(2, weight=0)

            self.location_frames.append(loc_frame)

            rank_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS["body_bold"],
                foreground=COLORS["text_secondary"],
                width=3,
            )
            rank_label.grid(row=0, column=0, sticky="w")

            name_label = ttk.Label(
                loc_frame, text="", font=FONTS["subheading"], anchor="w"
            )
            name_label.grid(row=0, column=1, sticky="ew", padx=(PADDING["small"], 0))

            score_label = ttk.Label(loc_frame, text="", font=FONTS["small"], anchor="w")
            score_label.grid(row=1, column=1, sticky="ew", padx=(PADDING["small"], 0))

            details_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS["small"],
                foreground=COLORS["text_secondary"],
                anchor="nw",
                justify="left",
                wraplength=280,
            )
            details_label.grid(
                row=2,
                column=1,
                sticky="nw",
                pady=(PADDING["tiny"], 0),
                padx=(PADDING["small"], 0),
            )

            self.side_panel_entries.append(
                (rank_label, name_label, score_label, details_label)
            )

    def _setup_main_table(self):
        """Setup the main table."""
        self.main_content_container = ttk.Frame(self.main_frame)
        self.main_content_container.grid(row=2, column=1, sticky="nsew")
        self.main_content_container.columnconfigure(0, weight=1)
        self.main_content_container.rowconfigure(0, weight=0)  # Selectors
        self.main_content_container.rowconfigure(1, weight=1)  # Table

        table_frame = ttk.Frame(
            self.main_content_container, style="Card.TFrame", padding=PADDING["small"]
        )
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("Time", "Temp", "Wind", "Clouds", "Rain", "Humidity")
        self.main_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20,
            style="Custom.Treeview",
        )
        self.main_table.grid(row=0, column=0, sticky="nsew")

        # Configure row colors
        self.main_table.tag_configure("Excellent", foreground=COLORS["excellent"])
        self.main_table.tag_configure("VeryGood", foreground=COLORS["very_good"])
        self.main_table.tag_configure("Good", foreground=COLORS["good"])
        self.main_table.tag_configure("Fair", foreground=COLORS["fair"])
        self.main_table.tag_configure("Poor", foreground=COLORS["poor"])

        # Column configuration
        col_configs = {
            "Time": {"width": 100, "anchor": "center", "stretch": False},
            "Temp": {"width": 120, "anchor": "center", "stretch": True},
            "Wind": {"width": 120, "anchor": "center", "stretch": True},
            "Clouds": {"width": 120, "anchor": "center", "stretch": True},
            "Rain": {"width": 120, "anchor": "center", "stretch": True},
            "Humidity": {"width": 120, "anchor": "center", "stretch": True},
        }

        headings = {
            "Time": "Time",
            "Temp": "Temperature",
            "Wind": "Wind Speed",
            "Clouds": "Cloud Coverage",
            "Rain": "Precipitation",
            "Humidity": "Humidity",
        }

        for col in columns:
            config = col_configs[col]
            self.main_table.heading(col, text=headings[col])
            self.main_table.column(
                col,
                anchor=config["anchor"],
                width=config["width"],
                minwidth=config["width"],
                stretch=config["stretch"],
            )

    def _start_data_loading(self):
        """Start loading weather data in a background thread."""
        self._update_status("Loading weather data...")
        self.load_generation += 1

        loading_thread = threading.Thread(
            target=self._load_all_forecasts_threaded,
            args=(self.load_generation,)
        )
        loading_thread.daemon = True
        loading_thread.start()

    def _load_all_forecasts_threaded(self, generation_id: int):
        """Load all forecasts in a background thread."""
        loaded_count = 0

        for loc_key, loc in self.current_locations.items():
            # Check if this thread is still relevant
            if generation_id != self.load_generation:
                return

            try:
                progress = (loaded_count / self.total_locations) * 100
                self.root.after(0, lambda: self.progress_var.set(progress))
                self.root.after(
                    0, lambda: self._update_status(f"Loading {loc.name}...")
                )

                raw = fetch_weather_data(loc)

                # Check again before processing/storing
                if generation_id != self.load_generation:
                    return

                if raw is not None:
                    processed = process_forecast(raw, loc.name)
                    if processed:
                        self.all_location_processed[loc_key] = processed
                        self.loaded_locations.add(loc_key)
                    else:
                        self.loading_errors[loc_key] = "Failed to process forecast data"
                else:
                    self.loading_errors[loc_key] = "Failed to fetch weather data"

            except Exception as e:
                self.loading_errors[loc_key] = f"Error: {str(e)}"

            loaded_count += 1

        self.root.after(0, lambda: self._on_loading_complete(generation_id))

    def _on_loading_complete(self, generation_id: int):
        """Handle completion of data loading."""
        if generation_id != self.load_generation:
            return

        self.progress_var.set(100)

        loaded_count = len(self.loaded_locations)
        error_count = len(self.loading_errors)

        if loaded_count > 0:
            self._update_status(
                f"Loaded {loaded_count} locations successfully"
                + (f" ({error_count} failed)" if error_count > 0 else "")
            )
            self._populate_location_selector()
            self.subtitle_label.config(
                text=f"Weather data for {loaded_count} locations"
            )
        else:
            self._update_status("Failed to load any weather data")
            self.subtitle_label.config(text="No weather data available")
            # Don't show error box if we just switched groups and failed some,
            # unless ALL failed.
            if error_count == self.total_locations:
                messagebox.showerror(
                    "Error",
                    "Failed to load weather data. Please check your internet connection.",
                )

        self.root.after(2000, self.progress_bar.grid_remove)

    def _update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.config(text=message)

    def _populate_location_selector(self):
        """Populate the location selector with loaded data."""
        if not self.loaded_locations:
            return

        location_names = [self.current_locations[loc_key].name for loc_key in self.loaded_locations]
        location_names.sort()  # Sort alphabetically for better UX

        self.location_dropdown["values"] = location_names
        if location_names:
            self.location_var.set(location_names[0])
            self.on_location_change()

    def on_group_change(self, event=None):
        """Handle location group selection change."""
        try:
            group_name = self.group_var.get()
            if not group_name or group_name not in LOCATION_GROUPS:
                return

            # Switch location set
            self.current_locations = LOCATION_GROUPS[group_name]
            self.total_locations = len(self.current_locations)

            # Reset data storage
            self.all_location_processed = {}
            self.loaded_locations = set()
            self.loading_errors = {}
            self.selected_location_key = ""
            self.selected_date = None
            self.date_map = {}

            # Reset UI elements
            self.location_var.set("")
            self.location_dropdown["values"] = []
            self.date_var.set("")
            self.date_dropdown["values"] = []
            self.main_table.delete(*self.main_table.get_children())

            # Clear side panel
            for (rank_label, name_label, score_label, details_label) in self.side_panel_entries:
                rank_label.config(text="")
                name_label.config(text="")
                score_label.config(text="")
                details_label.config(text="")

            # Show progress bar and start loading
            self.progress_bar.grid()
            self.subtitle_label.config(text="Loading weather data...")
            self._start_data_loading()

            self._update_status(f"Switched to {group_name} locations")

        except Exception as e:
            self._update_status(f"Error changing region: {str(e)}")

    def on_location_change(self, event=None):
        """Handle location selection change."""
        try:
            selected_name = self.location_var.get()
            if not selected_name:
                return

            # Find the selected location key
            self.selected_location_key = next(
                (key for key, loc in self.current_locations.items() if loc.name == selected_name), ""
            )

            if not self.selected_location_key:
                self._update_status(f"Location '{selected_name}' not found")
                return

            # Update date selector while preserving selection if possible
            previous_date = self.selected_date
            self._populate_date_selector()

            # Try to maintain the same date if available
            if previous_date and previous_date in self.date_map.values():
                date_str = next(
                    (
                        d_str
                        for d_str, d_obj in self.date_map.items()
                        if d_obj == previous_date
                    ),
                    None,
                )
                if date_str:
                    self.date_var.set(date_str)
                    self.selected_date = previous_date

            self._update_displays()
            self._update_status(f"Selected {selected_name}")

        except Exception as e:
            self._update_status(f"Error changing location: {str(e)}")

    def _populate_date_selector(self):
        """Populate the date selector."""
        try:
            if not self.selected_location_key:
                self.date_dropdown["values"] = []
                self.date_map = {}
                return

            processed = self.all_location_processed.get(self.selected_location_key)
            if not processed:
                self.date_dropdown["values"] = []
                self.date_map = {}
                return

            available_dates = get_available_dates(processed)
            if not available_dates:
                self.date_dropdown["values"] = []
                self.date_map = {}
                return

            self.date_map = {format_date(d): d for d in available_dates}
            date_strs = list(self.date_map.keys())

            self.date_dropdown["values"] = date_strs
            if date_strs:
                self.date_var.set(date_strs[0])
                self.on_date_change()

        except Exception as e:
            self._update_status(f"Error loading dates: {str(e)}")

    def on_date_change(self, event=None):
        """Handle date selection change."""
        try:
            selected_str = self.date_var.get()
            if not selected_str:
                return

            self.selected_date = self.date_map.get(selected_str)
            if not self.selected_date:
                return

            self._update_displays()
            self._update_status(f"Showing data for {selected_str}")

        except Exception as e:
            self._update_status(f"Error changing date: {str(e)}")

    def _update_displays(self):
        """Update both side panel and main table."""
        try:
            self._update_side_panel()
            self._update_main_table()
        except Exception as e:
            self._update_status(f"Error updating displays: {str(e)}")

    def _update_side_panel(self):
        """Update the side panel."""
        # Clear existing entries
        for (
            rank_label,
            name_label,
            score_label,
            details_label,
        ) in self.side_panel_entries:
            rank_label.config(text="")
            name_label.config(text="")
            score_label.config(text="")
            details_label.config(text="")

        if not self.selected_date:
            return

        try:
            top_locs = get_top_locations_for_date(
                self.all_location_processed, self.selected_date, top_n=10
            )

            for i, (rank_label, name_label, score_label, details_label) in enumerate(
                self.side_panel_entries
            ):
                if i < len(top_locs):
                    loc_data = top_locs[i]
                    self._populate_location_entry(
                        i + 1,
                        loc_data,
                        rank_label,
                        name_label,
                        score_label,
                        details_label,
                    )

        except Exception as e:
            self._update_status(f"Error updating side panel: {str(e)}")

    def _populate_location_entry(
        self,
        rank: int,
        loc_data: Dict[str, Any],
        rank_label: ttk.Label,
        name_label: ttk.Label,
        score_label: ttk.Label,
        details_label: ttk.Label,
    ):
        """Populate a single location entry in the side panel."""
        rank_label.config(text=f"#{rank}")
        name_label.config(text=loc_data["location_name"])

        total_score = loc_data.get("raw_score", loc_data.get("avg_score", 0))
        rating = get_rating_info(total_score)
        color = get_rating_color(rating)

        normalized = normalize_score(total_score)
        score_text = f"Score: {normalized}/100"

        if self.show_scores.get():
            score_text += f" (Raw: {total_score:.1f}, {rating})"
        else:
            score_text += f" ({rating})"

        score_label.config(text=score_text, foreground=color)

        # Format details
        best_block = loc_data.get("optimal_block")
        if best_block:
            start_str = best_block["start"].strftime("%H:%M")
            end_str = best_block["end"].strftime("%H:%M")

            temp_val = best_block.get("temp")
            wind_val = best_block.get("wind")
            precip_val = best_block.get("precip")

            # Fix newline formatting in ternary
            details = (
                f"Best time: {start_str} - {end_str}\n" +
                (f"Temp: {temp_val:.1f}°C\n" if temp_val is not None else "Temp: N/A\n") +
                (f"Wind: {wind_val:.1f} km/h\n" if wind_val is not None else "Wind: N/A\n") +
                (f"Rain: {precip_val:.1f} mm" if precip_val is not None else "Rain: 0.0 mm")
            )
        else:
            details = "No optimal block found"

        details_label.config(text=details)

    def _update_main_table(self):
        """Update the main table with data for the selected location."""
        # Clear existing items
        self.main_table.delete(*self.main_table.get_children())

        if not self.selected_location_key or not self.selected_date:
            return

        try:
            processed = self.all_location_processed.get(self.selected_location_key)
            if not processed:
                return

            time_blocks = get_time_blocks_for_date(processed, self.selected_date)

            for block in time_blocks:
                # Format time nicely (e.g. 14:00)
                time_str = block.time.strftime("%H:%M")

                values = (
                    time_str,
                    f"{block.temp:.1f}°C" if block.temp is not None else "N/A",
                    f"{block.wind:.1f} km/h" if block.wind is not None else "N/A",
                    f"{block.cloud_coverage:.0f}%" if block.cloud_coverage is not None else "N/A",
                    f"{block.precipitation_amount:.1f} mm" if block.precipitation_amount is not None else "0.0 mm",
                    f"{block.relative_humidity:.0f}%" if block.relative_humidity is not None else "N/A",
                )

                # Determine row color based on individual block score/rating
                # Calculate a rough score for the block to determine color
                score = block.total_score
                rating = get_rating_info(score)

                # Using tags to color the row
                tag = rating.replace(" ", "")  # Remove spaces for tag name
                self.main_table.insert("", "end", values=values, tags=(tag,))

        except Exception as e:
            self._update_status(f"Error updating table: {str(e)}")


def main():
    """Application entry point."""
    try:
        app = WeatherHelperApp()
        app.root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"An unexpected error occurred: {str(e)}")
