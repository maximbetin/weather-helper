"""
Main GUI application class for the weather helper.
Handles window setup and main widget initialization with enhanced UX.
"""

import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import date, datetime, timezone
from tkinter import ttk
from typing import Any, Dict, List, Optional

from src.core.config import get_timezone
from src.core.evaluation import get_available_dates, get_rating_info, get_time_blocks_for_date, get_top_locations_for_date, process_forecast
from src.core.locations import LOCATIONS
from src.core.weather_api import fetch_weather_data
from src.gui.formatting import add_tooltip, format_date, format_percentage, format_temperature, format_wind_speed
from src.gui.themes import COLORS, FONTS, PADDING, apply_theme, get_rating_color

class WeatherHelperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Weather Helper")
        self.root.minsize(1200, 750)
        apply_theme(self.root)

        # Initialize data and UI state
        self._init_data_storage()
        self._init_loading_state()
        self._setup_ui()

        # Start loading data asynchronously
        self.root.after(100, self._start_data_loading)

    def _init_data_storage(self):
        """Initialize data storage attributes."""
        self.all_location_processed: Dict[str, Any] = {}
        self.selected_location_key: Optional[str] = None
        self.selected_date = None
        self.date_map: Dict[str, Any] = {}
        self.loading_errors: Dict[str, str] = {}
        self.show_scores = tk.BooleanVar(value=False)  # Add toggle for score visibility

    def _init_loading_state(self):
        """Initialize loading state management."""
        self.is_loading = False
        self.loaded_locations = set()
        self.total_locations = len(LOCATIONS)

    def _setup_ui(self):
        """Setup the main UI layout and widgets."""
        self._setup_window()
        self._create_main_layout()
        self._setup_title_area()
        self._setup_status_bar()
        self._setup_main_table()  # Create main content container first
        self._setup_selectors()   # Then add selectors to it
        self._setup_side_panel()  # Finally setup side panel

    def _setup_window(self):
        """Configure the main window settings with better positioning."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1400  # Increased for better layout
        window_height = 900  # Increased for better content visibility

        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Set minimum window size to ensure proper layout
        self.root.minsize(1300, 850)

        # Configure resizing behavior
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _create_main_layout(self):
        """Create the main layout structure."""
        self.main_frame = ttk.Frame(self.root, padding=PADDING['large'])
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for proper resizing
        self.main_frame.columnconfigure(0, weight=0, minsize=360)  # Side panel - optimized width
        self.main_frame.columnconfigure(1, weight=1)  # Main content

        # Row configuration - sidebar starts from row 1
        self.main_frame.rowconfigure(0, weight=0)  # Title
        self.main_frame.rowconfigure(1, weight=1)  # Content area (sidebar and main table)
        self.main_frame.rowconfigure(2, weight=0)  # Status bar

    def _setup_title_area(self):
        """Setup the compact title area."""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, PADDING['small']))
        title_frame.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(
            title_frame,
            text="Weather Helper",
            style='Title.TLabel',
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

        # Subtitle with current info
        self.subtitle_label = ttk.Label(
            title_frame,
            text="Loading weather data...",
            style='Secondary.TLabel',
            anchor="center"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="ew", pady=(PADDING['small'], 0))

    def _setup_status_bar(self):
        """Setup the status bar for better user feedback."""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(PADDING['medium'], 0))
        self.status_frame.columnconfigure(1, weight=1)

        # Progress bar for loading
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode='determinate',
            variable=self.progress_var,
            length=200
        )
        self.progress_bar.grid(row=0, column=0, padx=(0, PADDING['medium']))

        # Status text
        self.status_label = ttk.Label(
            self.status_frame,
            text="Initializing...",
            style='Status.TLabel',
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, sticky="ew")

    def _setup_selectors(self):
        """Setup enhanced location and date selectors in new layout."""
        # Selectors in main content area
        selector_frame = ttk.Frame(self.main_content_container, style='Card.TFrame', padding=PADDING['medium'])
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, PADDING['small']))
        selector_frame.columnconfigure(1, weight=1)
        selector_frame.columnconfigure(3, weight=1)

        # Location selector with improved styling
        ttk.Label(
            selector_frame,
            text="Location:",
            font=FONTS['body_bold']
        ).grid(row=0, column=0, padx=(0, PADDING['small']), sticky="w")

        self.location_var = tk.StringVar()
        self.location_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.location_var,
            state="readonly",
            font=FONTS['body'],
            width=25
        )
        self.location_dropdown.grid(row=0, column=1, sticky="ew", padx=(0, PADDING['large']))
        self.location_dropdown.bind("<<ComboboxSelected>>", self.on_location_change)
        add_tooltip(self.location_dropdown, "Select a location to view weather forecast")

        # Date selector with improved styling
        ttk.Label(
            selector_frame,
            text="Date:",
            font=FONTS['body_bold']
        ).grid(row=0, column=2, padx=(0, PADDING['small']), sticky="w")

        self.date_var = tk.StringVar()
        self.date_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.date_var,
            state="readonly",
            font=FONTS['body'],
            width=20
        )
        self.date_dropdown.grid(row=0, column=3, sticky="ew")
        self.date_dropdown.bind("<<ComboboxSelected>>", self.on_date_change)
        add_tooltip(self.date_dropdown, "Select a date to view hourly weather data")

        # Score visibility toggle checkbox
        self.score_toggle = ttk.Checkbutton(
            selector_frame,
            text="Show scoring values",
            variable=self.show_scores,
            command=self._on_score_toggle_change,
            style='Toggle.TCheckbutton'
        )
        self.score_toggle.grid(row=1, column=0, columnspan=4, sticky="w", pady=(PADDING['small'], 0))
        add_tooltip(self.score_toggle, "Toggle to show/hide the scoring values for each weather parameter")

    def _on_score_toggle_change(self):
        """Handle the score visibility toggle."""
        self._update_displays()

    def _setup_side_panel(self):
        """Setup the side panel with enhanced visual design."""
        # Create side panel with proper styling
        self.side_panel = ttk.Frame(self.main_frame, style='Sidebar.TFrame', padding=PADDING['small'])
        self.side_panel.grid(row=1, column=0, sticky="nsew", padx=(0, PADDING['small']))
        self.side_panel.columnconfigure(0, weight=1)

        # Title for side panel
        title_label = ttk.Label(
            self.side_panel,
            text="Top 5 Locations",
            style='Heading.TLabel',
            anchor="center"
        )
        title_label.grid(row=0, column=0, sticky="ew", pady=(0, PADDING['small']))

        # Initialize list to store location entries
        self.location_frames = []
        self.side_panel_entries = []

        for i in range(5):
            # Create container frame for each location with minimal padding
            loc_frame = ttk.Frame(self.side_panel, padding=(PADDING['small'], PADDING['small']))
            loc_frame.grid(row=i + 1, column=0, sticky="ew", pady=PADDING['tiny'])
            loc_frame.columnconfigure(1, weight=1)
            loc_frame.rowconfigure(0, weight=0)
            loc_frame.rowconfigure(1, weight=0)
            loc_frame.rowconfigure(2, weight=0)  # Changed from weight=1 to weight=0

            self.location_frames.append(loc_frame)

            # Rank number with better styling
            rank_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS['body_bold'],
                foreground=COLORS['text_secondary'],
                width=3
            )
            rank_label.grid(row=0, column=0, sticky="w")

            # Location name (larger text)
            name_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS['subheading'],
                anchor="w"
            )
            name_label.grid(row=0, column=1, sticky="ew", padx=(PADDING['small'], 0))

            # Score (smaller text)
            score_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS['small'],
                anchor="w"
            )
            score_label.grid(row=1, column=1, sticky="ew", padx=(PADDING['small'], 0))

            # Best time details aligned properly under location name
            details_label = ttk.Label(
                loc_frame,
                text="",
                font=FONTS['small'],
                foreground=COLORS['text_secondary'],
                anchor="nw",
                justify="left",
                wraplength=280  # Increased for better text display
            )
            details_label.grid(row=2, column=1, sticky="nw", pady=(PADDING['tiny'], 0), padx=(PADDING['small'], 0))

            self.side_panel_entries.append((rank_label, name_label, score_label, details_label))

    def _setup_main_table(self):
        """Setup the enhanced main table with better styling."""
        # Create main content container for selectors and table
        self.main_content_container = ttk.Frame(self.main_frame)
        self.main_content_container.grid(row=1, column=1, sticky="nsew")
        self.main_content_container.columnconfigure(0, weight=1)
        self.main_content_container.rowconfigure(0, weight=0)  # Selectors
        self.main_content_container.rowconfigure(1, weight=1)  # Table

        # Table container
        table_frame = ttk.Frame(self.main_content_container, style='Card.TFrame', padding=PADDING['small'])
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Simplified table with essential data and scores in parentheses
        columns = (
            "Time", "Temp", "Wind", "Clouds", "Rain"
        )
        self.main_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20,
            style='Custom.Treeview'
        )
        self.main_table.grid(row=0, column=0, sticky="nsew")

        # Configure row colors FIRST before any data is added
        self.main_table.tag_configure('Excellent', foreground=COLORS['excellent'])
        self.main_table.tag_configure('VeryGood', foreground=COLORS['very_good'])
        self.main_table.tag_configure('Good', foreground=COLORS['good'])
        self.main_table.tag_configure('Fair', foreground=COLORS['fair'])
        self.main_table.tag_configure('Poor', foreground=COLORS['poor'])

        # Enhanced column configuration with proper alignments
        col_configs = {
            "Time": {"width": 100, "anchor": "center", "stretch": False},
            "Temp": {"width": 120, "anchor": "center", "stretch": True},
            "Wind": {"width": 120, "anchor": "center", "stretch": True},
            "Clouds": {"width": 120, "anchor": "center", "stretch": True},
            "Rain": {"width": 120, "anchor": "center", "stretch": True}
        }

        # Set column headings with clear labels
        headings = {
            "Time": "Time",
            "Temp": "Temperature",
            "Wind": "Wind Speed",
            "Clouds": "Cloud Coverage",
            "Rain": "Precipitation"
        }

        for col in columns:
            config = col_configs[col]
            self.main_table.heading(col, text=headings[col])
            self.main_table.column(
                col,
                anchor=config["anchor"],
                width=config["width"],
                minwidth=config["width"],
                stretch=config["stretch"]
            )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.main_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_table.configure(yscrollcommand=scrollbar.set)

    def _start_data_loading(self):
        """Start loading weather data in a background thread."""
        self.is_loading = True
        self._update_status("Loading weather data...")

        # Use threading to prevent UI freezing
        loading_thread = threading.Thread(target=self._load_all_forecasts_threaded)
        loading_thread.daemon = True
        loading_thread.start()

    def _load_all_forecasts_threaded(self):
        """Load all forecasts in a background thread."""
        loaded_count = 0

        for loc_key, loc in LOCATIONS.items():
            try:
                # Update progress
                progress = (loaded_count / self.total_locations) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda l=loc.name: self._update_status(f"Loading {l}..."))

                raw = fetch_weather_data(loc)
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

        # Update UI on main thread when complete
        self.root.after(0, self._on_loading_complete)

    def _on_loading_complete(self):
        """Handle completion of data loading."""
        self.is_loading = False
        self.progress_var.set(100)

        loaded_count = len(self.loaded_locations)
        error_count = len(self.loading_errors)

        if loaded_count > 0:
            self._update_status(f"Loaded {loaded_count} locations successfully" +
                                (f" ({error_count} failed)" if error_count > 0 else ""))
            self._populate_location_selector()
            self.subtitle_label.config(text=f"Weather data for {loaded_count} locations")
        else:
            self._update_status("Failed to load any weather data")
            self.subtitle_label.config(text="No weather data available")
            messagebox.showerror("Error", "Failed to load weather data. Please check your internet connection.")

        # Hide progress bar after a delay
        self.root.after(2000, lambda: self.progress_bar.grid_remove())

    def _update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.config(text=message)

    def _populate_location_selector(self):
        """Populate the location selector with loaded data."""
        if not self.loaded_locations:
            return

        location_names = [
            LOCATIONS[loc_key].name
            for loc_key in self.loaded_locations
            if loc_key in LOCATIONS
        ]
        location_names.sort()  # Sort alphabetically for better UX

        self.location_dropdown['values'] = location_names
        if location_names:
            self.location_var.set(location_names[0])
            self.on_location_change()

    def on_location_change(self, event=None):
        """Handle location selection change with better error handling."""
        try:
            selected_name = self.location_var.get()
            if not selected_name:
                return

            # Find the selected location key
            self.selected_location_key = None
            for key, loc in LOCATIONS.items():
                if loc.name == selected_name:
                    self.selected_location_key = key
                    break

            if not self.selected_location_key:
                self._update_status(f"Location '{selected_name}' not found")
                return

            # Update date selector while preserving selection if possible
            previous_date = self.selected_date
            self._populate_date_selector()

            # Try to maintain the same date if available
            if previous_date and previous_date in self.date_map.values():
                for date_str, date_obj in self.date_map.items():
                    if date_obj == previous_date:
                        self.date_var.set(date_str)
                        self.selected_date = previous_date
                        break

            self._update_displays()
            self._update_status(f"Selected {selected_name}")

        except Exception as e:
            self._update_status(f"Error changing location: {str(e)}")

    def _populate_date_selector(self):
        """Populate the date selector with improved error handling."""
        try:
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
            if not available_dates:
                self.date_dropdown['values'] = []
                self.date_map = {}
                return

            # Create date mapping with better formatting
            self.date_map = {format_date(d): d for d in available_dates}
            date_strs = list(self.date_map.keys())

            self.date_dropdown['values'] = date_strs
            if date_strs:
                self.date_var.set(date_strs[0])
                self.on_date_change()

        except Exception as e:
            self._update_status(f"Error loading dates: {str(e)}")

    def on_date_change(self, event=None):
        """Handle date selection change with improved error handling."""
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
        """Update the side panel with enhanced visual design."""
        # Clear existing entries
        for rank_label, name_label, score_label, details_label in self.side_panel_entries:
            rank_label.config(text="")
            name_label.config(text="")
            score_label.config(text="")
            details_label.config(text="")

        if not self.selected_date:
            return

        try:
            top_locs = get_top_locations_for_date(
                self.all_location_processed,
                self.selected_date,
                top_n=5
            )

            for i, (rank_label, name_label, score_label, details_label) in enumerate(self.side_panel_entries):
                if i < len(top_locs):
                    loc_data = top_locs[i]
                    self._populate_location_entry(i + 1, loc_data, rank_label, name_label, score_label, details_label)

        except Exception as e:
            self._update_status(f"Error updating rankings: {str(e)}")

    def _populate_location_entry(self, rank: int, loc_data: Dict, rank_label: ttk.Label, name_label: ttk.Label, score_label: ttk.Label, details_label: ttk.Label):
        """Populate a single location entry in the side panel."""
        try:
            # Set rank number
            rank_label.config(text=f"{rank}.")

            # Get score and rating
            score = loc_data.get("combined_score", 0)
            rating = get_rating_info(score)
            score_color = get_rating_color(rating)

            # Set location name with color
            name_label.config(
                text=loc_data.get("location_name", "Unknown"),
                foreground=score_color,
                font=FONTS['subheading']
            )

            # Set score with conditional display
            if self.show_scores.get():
                score_text = f"{rating} ({score:.1f})"
            else:
                score_text = rating

            score_label.config(
                text=score_text,
                foreground=score_color,
                font=FONTS['small_bold']
            )

            # Set details with color
            details = self._get_location_details(loc_data)
            details_label.config(
                text=details,
                foreground=score_color
            )

        except Exception as e:
            rank_label.config(text="")
            name_label.config(text="Error")
            score_label.config(text="")
            details_label.config(text=str(e))

    def _filter_daylight_hours(self, hours_for_day: List, selected_date: date) -> List:
        """Filter hours for daylight and future times with consistent logic.

        Args:
            hours_for_day: List of hourly weather data
            selected_date: The selected date

        Returns:
            Filtered list of hours
        """
        local_tz = get_timezone()
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(local_tz)

        # Filter for daylight hours and future times
        if selected_date == now_local.date():
            # Show future hours, plus current hour if we're in the first half of it
            return [
                h for h in hours_for_day
                if 8 <= h.time.hour <= 20 and (
                    h.time.astimezone(local_tz) > now_local or
                    (h.time.astimezone(local_tz).hour == now_local.hour and now_local.minute < 30)
                )
            ]
        else:
            return [h for h in hours_for_day if 8 <= h.time.hour <= 20]

    def _get_location_details(self, loc_data: Dict) -> str:
        """Get formatted details for a location entry."""
        try:
            location_key = loc_data.get('location_key')
            if not location_key:
                return "No details available"

            processed = self.all_location_processed.get(location_key)
            if not processed or not self.selected_date:
                return "No forecast data"

            # Get hourly data for analysis
            daily_forecasts = processed.get("daily_forecasts", {})
            hours_for_day = daily_forecasts.get(self.selected_date, [])

            # Filter for daylight hours and future times
            filtered_blocks = self._filter_daylight_hours(hours_for_day, self.selected_date)

            if not filtered_blocks:
                return "No daylight data available"

            # Find optimal consistent block (same as Top 5 calculation)
            from src.core.evaluation import _find_optimal_consistent_block
            optimal_block = _find_optimal_consistent_block(filtered_blocks)

            if optimal_block:
                local_tz = get_timezone()
                start_time = optimal_block["start"].astimezone(local_tz).strftime('%H:%M')
                end_time = optimal_block["end"].astimezone(local_tz).strftime('%H:%M')
                duration = optimal_block.get("duration", 1)
                temp = optimal_block.get("temp")

                # Format based on duration
                if duration == 1:
                    # Single hour - make it clear
                    details = f"Best: {start_time} (1h)"
                else:
                    # Multiple hours - show range
                    details = f"{start_time}-{end_time} ({duration}h)"

                # Add practical outdoor activity info instead of weather symbols
                info_parts = []
                if temp is not None:
                    info_parts.append(f"{temp:.1f}°C")

                if info_parts:
                    details += f" | {' | '.join(info_parts)}"

            else:
                # If no optimal block found, show best single hour
                local_tz = get_timezone()
                best_hour = max(filtered_blocks, key=lambda h: h.total_score)
                time_str = best_hour.time.astimezone(local_tz).strftime('%H:%M')

                # Format single hour with practical info
                details = f"Best hour: {time_str}"
                info_parts = []
                if best_hour.temp is not None:
                    info_parts.append(f"{best_hour.temp:.1f}°C")

                if info_parts:
                    details += f" | {' | '.join(info_parts)}"

            return details

        except Exception:
            return "Error loading details"

    def _update_main_table(self):
        """Update the main table with enhanced formatting and error handling."""
        # Clear existing entries
        for row in self.main_table.get_children():
            self.main_table.delete(row)

        if not (self.selected_location_key and self.selected_date):
            return

        try:
            processed = self.all_location_processed.get(self.selected_location_key)
            if not processed:
                return

            time_blocks = get_time_blocks_for_date(processed, self.selected_date)
            if not time_blocks:
                return

            # Filter for daylight hours and future times
            filtered_blocks = self._filter_daylight_hours(time_blocks, self.selected_date)

            # Populate table with enhanced formatting
            for hour in filtered_blocks:
                self._add_table_row(hour)

        except Exception as e:
            self._update_status(f"Error updating table: {str(e)}")

    def _add_table_row(self, hour):
        """Add a single row to the main table with proper formatting."""
        try:
            # Format time with conditional score display
            if self.show_scores.get():
                time_str = f"{hour.time.strftime('%H:%M')} ({hour.total_score:+.0f})"
            else:
                time_str = hour.time.strftime('%H:%M')

            # Format values with conditional score display
            if self.show_scores.get():
                temp = f"{hour.temp:.1f}°C ({hour.temp_score:+.0f})" if hour.temp is not None else "N/A"
                wind = f"{hour.wind:.1f}m/s ({hour.wind_score:+.0f})" if hour.wind is not None else "N/A"
                clouds = f"{hour.cloud_coverage:.0f}% ({hour.cloud_score:+.0f})" if hour.cloud_coverage is not None else "N/A"
                rain = f"{hour.precipitation_amount:.1f}mm ({hour.precip_amount_score:+.0f})" if hour.precipitation_amount is not None else "N/A"
            else:
                temp = f"{hour.temp:.1f}°C" if hour.temp is not None else "N/A"
                wind = f"{hour.wind:.1f}m/s" if hour.wind is not None else "N/A"
                clouds = f"{hour.cloud_coverage:.0f}%" if hour.cloud_coverage is not None else "N/A"
                rain = f"{hour.precipitation_amount:.1f}mm" if hour.precipitation_amount is not None else "N/A"

            # Determine tag based on score thresholds
            if hour.total_score >= 12:
                tag = 'Excellent'
            elif hour.total_score >= 8:
                tag = 'VeryGood'
            elif hour.total_score >= 4:
                tag = 'Good'
            elif hour.total_score >= 1:
                tag = 'Fair'
            else:
                tag = 'Poor'

            # Insert row with proper tag
            self.main_table.insert(
                "", "end",
                values=(
                    time_str, temp, wind, clouds, rain
                ),
                tags=(tag,)
            )

        except Exception as e:
            # Add error row for debugging
            self.main_table.insert(
                "", "end",
                values=("Error", "Error", "Error", "Error", "Error"),
                tags=('Poor',)
            )

    def run(self):
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Critical Error", f"Application error: {str(e)}")

def main():
    """Main entry point for the application."""
    try:
        app = WeatherHelperApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start Weather Helper: {str(e)}")

if __name__ == "__main__":
    main()
