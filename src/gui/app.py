"""
Main GUI application class for the weather helper.
Handles window setup and main widget initialization.
"""

import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import date, datetime, timedelta
from tkinter import ttk
from typing import Any, Dict

from src.core.evaluation import (
    get_available_dates,
    get_time_blocks_for_date,
    get_top_locations_for_date,
    process_forecast,
)
from src.core.scoring import (
    ACTIVITY_BEACH_DAY,
    ACTIVITY_PROFILE_LABELS,
    DEFAULT_ACTIVITY_PROFILE,
    get_activity_profile_key,
    get_activity_profile_label,
    get_activity_score,
    get_rating_info,
    normalize_score,
)
from src.core.locations import LOCATIONS, LOCATION_GROUPS
from src.core.weather_api import fetch_weather_data
from src.gui.formatting import (
    add_tooltip,
    format_date,
    format_percentage,
    format_precipitation,
    format_temperature,
    format_time,
    format_wind_speed,
)
from src.gui.themes import COLORS, FONTS, PADDING, apply_theme, get_rating_color

DEFAULT_SCREEN_WIDTH = 1400
DEFAULT_SCREEN_HEIGHT = 900
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700
MAX_WINDOW_WIDTH = 1400
MAX_WINDOW_HEIGHT = 950
WINDOW_WIDTH_MARGIN = 120
WINDOW_HEIGHT_MARGIN = 160
PROGRESS_COMPLETE_PERCENT = 100
PROGRESS_HIDE_DELAY_MS = 2000
STARTUP_LOAD_DELAY_MS = 100
MAX_SIDE_PANEL_LOCATIONS = 10
SIDE_PANEL_WRAP_LENGTH = 260
RAIN_RISK_WARNING_PERCENT = 40
RAIN_AMOUNT_WARNING_MM = 0.5
DRY_RAIN_AMOUNT_MM = 0.1
DRY_RAIN_RISK_PERCENT = 25
BEACH_WIND_WARNING_SPEED = 8
BEACH_CALM_WIND_SPEED = 4
BEACH_GOOD_SUN_CLOUD_PERCENT = 45
HIKING_COMFORTABLE_WIND_SPEED = 5
HIKING_USABLE_LIGHT_CLOUD_PERCENT = 60
TABLE_COLUMNS = (
    "Time",
    "Temp",
    "Wind",
    "Clouds",
    "Rain",
    "RainChance",
    "Humidity",
    "Score",
)
TABLE_COLUMN_CONFIGS = {
    "Time": {"width": 100, "anchor": "center", "stretch": False},
    "Temp": {"width": 120, "anchor": "center", "stretch": True},
    "Wind": {"width": 120, "anchor": "center", "stretch": True},
    "Clouds": {"width": 120, "anchor": "center", "stretch": True},
    "Rain": {"width": 120, "anchor": "center", "stretch": True},
    "RainChance": {"width": 120, "anchor": "center", "stretch": True},
    "Humidity": {"width": 120, "anchor": "center", "stretch": True},
    "Score": {"width": 110, "anchor": "center", "stretch": True},
}
TABLE_HEADINGS = {
    "Time": "Time",
    "Temp": "Temperature",
    "Wind": "Wind Speed",
    "Clouds": "Cloud Coverage",
    "Rain": "Precipitation",
    "RainChance": "Rain Risk",
    "Humidity": "Humidity",
    "Score": "Profile Score",
}


class WeatherHelperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Weather Helper")
        self.root.minsize(1000, 700)
        apply_theme(self.root)

        # Initialize data and UI state
        self._init_data_storage()
        self._setup_ui()

        # Start loading data asynchronously
        self.root.after(STARTUP_LOAD_DELAY_MS, self._start_data_loading)

    def _init_data_storage(self):
        """Initialize data storage attributes."""
        self.all_location_processed: Dict[str, Any] = {}
        self.selected_location_key: str = ""
        self.selected_date = None
        self.date_map: Dict[str, date] = {}
        self.loading_errors: Dict[str, str] = {}
        self.show_scores = tk.BooleanVar(value=False)
        self.activity_profile_var = tk.StringVar(
            value=get_activity_profile_label(DEFAULT_ACTIVITY_PROFILE)
        )
        self.selected_activity_profile = DEFAULT_ACTIVITY_PROFILE
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
        screen_width, screen_height = self._screen_size()
        window_width, window_height = self._window_size(screen_width, screen_height)
        x, y = self._window_position(screen_width, screen_height, window_width, window_height)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        self._configure_root_grid()

    def _screen_size(self) -> tuple[int, int]:
        """Return validated screen dimensions."""
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        width = width if isinstance(width, (int, float)) else DEFAULT_SCREEN_WIDTH
        height = height if isinstance(height, (int, float)) else DEFAULT_SCREEN_HEIGHT
        return int(width), int(height)

    def _window_size(self, screen_width: int, screen_height: int) -> tuple[int, int]:
        """Return bounded window dimensions for the current screen."""
        width = min(MAX_WINDOW_WIDTH, max(MIN_WINDOW_WIDTH, screen_width - WINDOW_WIDTH_MARGIN))
        height = min(MAX_WINDOW_HEIGHT, max(MIN_WINDOW_HEIGHT, screen_height - WINDOW_HEIGHT_MARGIN))
        return width, height

    def _window_position(
        self, screen_width: int, screen_height: int, window_width: int, window_height: int
    ) -> tuple[int, int]:
        """Return coordinates that center the application window."""
        return (screen_width - window_width) // 2, (screen_height - window_height) // 2

    def _configure_root_grid(self):
        """Configure root grid weights."""
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
        title_frame = self._create_title_frame()
        self._create_title_label(title_frame)
        self._create_subtitle_label(title_frame)

    def _create_title_frame(self):
        """Create and grid the title frame."""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, PADDING["small"])
        )
        title_frame.columnconfigure(0, weight=1)
        return title_frame

    def _create_title_label(self, title_frame):
        """Create the main title label."""
        self.title_label = ttk.Label(
            title_frame, text="Weather Helper", style="Title.TLabel", anchor="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

    def _create_subtitle_label(self, title_frame):
        """Create the subtitle label."""
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
        self._create_status_frame()
        self._create_progress_bar()
        self._create_status_label()
        self._create_author_label()

    def _create_status_frame(self):
        """Create and grid the status frame."""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, PADDING["medium"])
        )
        self.status_frame.columnconfigure(1, weight=1)
        self.status_frame.columnconfigure(2, weight=0)  # For author label

    def _create_progress_bar(self):
        """Create the loading progress bar."""
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode="determinate",
            variable=self.progress_var,
            length=200,
        )
        self.progress_bar.grid(row=0, column=0, padx=(0, PADDING["medium"]))

    def _create_status_label(self):
        """Create the loading status label."""
        self.status_label = ttk.Label(
            self.status_frame, text="Initializing...", style="Status.TLabel", anchor="w"
        )
        self.status_label.grid(row=0, column=1, sticky="ew")

    def _create_author_label(self):
        """Create the status-bar author label."""
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
        selector_frame = self._create_selector_frame()
        self._configure_selector_columns(selector_frame)
        self._setup_region_selector(selector_frame)
        self._setup_location_selector(selector_frame)
        self._setup_date_selector(selector_frame)
        self._setup_activity_selector(selector_frame)
        self._setup_score_toggle(selector_frame)

    def _create_selector_frame(self):
        """Create the selector container."""
        selector_frame = ttk.Frame(
            self.main_content_container, style="Card.TFrame", padding=PADDING["medium"]
        )
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, PADDING["small"]))
        return selector_frame

    def _configure_selector_columns(self, selector_frame):
        """Configure selector column expansion."""
        selector_frame.columnconfigure(1, weight=1)
        selector_frame.columnconfigure(3, weight=1)
        selector_frame.columnconfigure(5, weight=1)

    def _setup_region_selector(self, selector_frame):
        """Create the region selector."""
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

    def _setup_location_selector(self, selector_frame):
        """Create the location selector."""
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

    def _setup_date_selector(self, selector_frame):
        """Create the date selector."""
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

    def _setup_activity_selector(self, selector_frame):
        """Create the activity selector."""
        self._create_activity_label(selector_frame)
        self.activity_dropdown = self._create_activity_dropdown(selector_frame)
        self._grid_activity_dropdown()
        self.activity_dropdown.bind("<<ComboboxSelected>>", self.on_activity_change)
        add_tooltip(
            self.activity_dropdown,
            "Choose whether to rank conditions for hiking or beach plans",
        )

    def _create_activity_label(self, selector_frame):
        """Create the activity selector label."""
        ttk.Label(selector_frame, text="Activity:", font=FONTS["body_bold"]).grid(
            row=1, column=0, padx=(0, PADDING["small"]), sticky="w"
        )

    def _create_activity_dropdown(self, selector_frame):
        """Create the activity combobox."""
        return ttk.Combobox(
            selector_frame,
            textvariable=self.activity_profile_var,
            state="readonly",
            font=FONTS["body"],
            width=15,
            values=list(ACTIVITY_PROFILE_LABELS.values()),
        )

    def _grid_activity_dropdown(self):
        """Grid the activity combobox."""
        self.activity_dropdown.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, PADDING["large"]),
            pady=(PADDING["small"], 0),
        )

    def _setup_score_toggle(self, selector_frame):
        """Create the scoring visibility toggle."""
        self.score_toggle = ttk.Checkbutton(
            selector_frame,
            text="Show scoring values",
            variable=self.show_scores,
            command=self._on_score_toggle_change,
            style="Toggle.TCheckbutton",
        )
        self.score_toggle.grid(
            row=1, column=2, columnspan=4, sticky="w", pady=(PADDING["small"], 0)
        )
        add_tooltip(
            self.score_toggle,
            "Toggle to show/hide the scoring values for each weather parameter",
        )

    def _on_score_toggle_change(self):
        """Handle the score visibility toggle."""
        self._update_displays()

    def _setup_side_panel(self):
        """Setup the side panel with scrollbar."""
        self._create_side_panel_container()
        canvas, scrollbar = self._create_side_panel_scroll_widgets()
        self._configure_side_panel_scrolling(canvas, scrollbar)
        self._create_side_panel_title()
        self._create_side_panel_entries()

    def _create_side_panel_container(self):
        """Create the side panel outer container."""
        self.side_panel_container = ttk.Frame(self.main_frame, style="Sidebar.TFrame")
        self.side_panel_container.grid(
            row=2, column=0, sticky="nsew", padx=(0, PADDING["small"])
        )
        self.side_panel_container.columnconfigure(0, weight=1)
        self.side_panel_container.rowconfigure(0, weight=1)

    def _create_side_panel_scroll_widgets(self):
        """Create canvas, scrollbar, and scrollable frame."""
        canvas = tk.Canvas(self.side_panel_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.side_panel_container, orient="vertical", command=canvas.yview
        )
        self.side_panel = ttk.Frame(
            canvas, style="Sidebar.TFrame", padding=PADDING["small"]
        )
        self._side_panel_canvas_frame = canvas.create_window(
            (0, 0), window=self.side_panel, anchor="nw"
        )
        return canvas, scrollbar

    def _configure_side_panel_scrolling(self, canvas, scrollbar):
        """Wire side-panel scrolling behavior."""
        self.side_panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: self._resize_side_panel_canvas(canvas, e))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.bind_all("<MouseWheel>", lambda e: self._scroll_side_panel(canvas, e))

    def _resize_side_panel_canvas(self, canvas, event):
        """Resize the inner side-panel frame to canvas width."""
        canvas.itemconfig(self._side_panel_canvas_frame, width=event.width)

    def _scroll_side_panel(self, canvas, event):
        """Scroll the side panel from a mouse wheel event."""
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _create_side_panel_title(self):
        """Create the side panel heading."""
        self.side_panel_title_label = ttk.Label(
            self.side_panel,
            text=self._get_side_panel_title(),
            style="Heading.TLabel",
            anchor="center",
        )
        self.side_panel_title_label.grid(
            row=0, column=0, sticky="ew", pady=(0, PADDING["small"])
        )

    def _create_side_panel_entries(self):
        """Create reusable side-panel location rows."""
        self.location_frames = []
        self.side_panel_entries = []
        for index in range(MAX_SIDE_PANEL_LOCATIONS):
            entry = self._create_side_panel_entry(index)
            self.side_panel_entries.append(entry)

    def _create_side_panel_entry(self, index: int):
        """Create one reusable side-panel location row."""
        loc_frame = self._create_location_frame(index)
        rank_label = self._create_rank_label(loc_frame)
        name_label = self._create_name_label(loc_frame)
        score_label = self._create_score_label(loc_frame)
        details_label = self._create_details_label(loc_frame)
        return rank_label, name_label, score_label, details_label

    def _create_location_frame(self, index: int):
        """Create the frame for one side-panel row."""
        loc_frame = ttk.Frame(self.side_panel, padding=(PADDING["small"], PADDING["small"]))
        loc_frame.grid(row=index + 1, column=0, sticky="ew", pady=PADDING["tiny"])
        loc_frame.columnconfigure(1, weight=1)
        for row_index in range(3):
            loc_frame.rowconfigure(row_index, weight=0)
        self.location_frames.append(loc_frame)
        return loc_frame

    def _create_rank_label(self, loc_frame):
        """Create a side-panel rank label."""
        label = ttk.Label(
            loc_frame, text="", font=FONTS["body_bold"],
            foreground=COLORS["text_secondary"], width=3
        )
        label.grid(row=0, column=0, sticky="w")
        return label

    def _create_name_label(self, loc_frame):
        """Create a side-panel location name label."""
        label = ttk.Label(loc_frame, text="", font=FONTS["subheading"], anchor="w")
        label.grid(row=0, column=1, sticky="ew", padx=(PADDING["small"], 0))
        return label

    def _create_score_label(self, loc_frame):
        """Create a side-panel score label."""
        label = ttk.Label(loc_frame, text="", font=FONTS["small"], anchor="w")
        label.grid(row=1, column=1, sticky="ew", padx=(PADDING["small"], 0))
        return label

    def _create_details_label(self, loc_frame):
        """Create a side-panel detail label."""
        label = ttk.Label(
            loc_frame, text="", font=FONTS["small"],
            foreground=COLORS["text_secondary"], anchor="nw",
            justify="left", wraplength=SIDE_PANEL_WRAP_LENGTH
        )
        label.grid(row=2, column=1, sticky="nw", pady=(PADDING["tiny"], 0), padx=(PADDING["small"], 0))
        return label

    def _setup_main_table(self):
        """Setup the main table."""
        self._create_main_content_container()
        table_frame = self._create_table_frame()
        self._create_main_treeview(table_frame)
        self._configure_table_row_tags()
        self._configure_table_columns()

    def _create_main_content_container(self):
        """Create the main content container."""
        self.main_content_container = ttk.Frame(self.main_frame)
        self.main_content_container.grid(row=2, column=1, sticky="nsew")
        self.main_content_container.columnconfigure(0, weight=1)
        self.main_content_container.rowconfigure(0, weight=0)  # Selectors
        self.main_content_container.rowconfigure(1, weight=1)  # Table

    def _create_table_frame(self):
        """Create the table frame."""
        table_frame = ttk.Frame(
            self.main_content_container, style="Card.TFrame", padding=PADDING["small"]
        )
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        return table_frame

    def _create_main_treeview(self, table_frame):
        """Create the hourly forecast treeview."""
        self.main_table = ttk.Treeview(
            table_frame,
            columns=TABLE_COLUMNS,
            show="headings",
            height=20,
            style="Custom.Treeview",
        )
        self.main_table.grid(row=0, column=0, sticky="nsew")

    def _configure_table_row_tags(self):
        """Configure rating colors for table rows."""
        self.main_table.tag_configure("Excellent", foreground=COLORS["excellent"])
        self.main_table.tag_configure("VeryGood", foreground=COLORS["very_good"])
        self.main_table.tag_configure("Good", foreground=COLORS["good"])
        self.main_table.tag_configure("Fair", foreground=COLORS["fair"])
        self.main_table.tag_configure("Poor", foreground=COLORS["poor"])

    def _configure_table_columns(self):
        """Configure table headings and column sizing."""
        for col in TABLE_COLUMNS:
            config = TABLE_COLUMN_CONFIGS[col]
            self.main_table.heading(col, text=TABLE_HEADINGS[col])
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
            if self._is_stale_generation(generation_id):
                return
            try:
                self._queue_location_loading_status(loc.name, loaded_count)
                self._load_single_forecast(loc_key, loc)
                if self._is_stale_generation(generation_id):
                    return
            except Exception as e:
                self.loading_errors[loc_key] = f"Error: {str(e)}"
            loaded_count += 1
        self.root.after(0, lambda: self._on_loading_complete(generation_id))

    def _is_stale_generation(self, generation_id: int) -> bool:
        """Return True when a background load should stop."""
        return generation_id != self.load_generation

    def _queue_location_loading_status(self, location_name: str, loaded_count: int):
        """Queue progress and status updates on the UI thread."""
        progress = (loaded_count / self.total_locations) * PROGRESS_COMPLETE_PERCENT
        self.root.after(0, lambda: self.progress_var.set(progress))
        self.root.after(0, lambda: self._update_status(f"Loading {location_name}..."))

    def _load_single_forecast(self, loc_key: str, loc):
        """Fetch, process, and store a single location forecast."""
        raw_forecast = fetch_weather_data(loc)
        if raw_forecast is None:
            self.loading_errors[loc_key] = "Failed to fetch weather data"
            return
        self._store_processed_forecast(loc_key, loc.name, raw_forecast)

    def _store_processed_forecast(self, loc_key: str, location_name: str, raw_forecast):
        """Store a processed forecast or record a processing error."""
        processed = process_forecast(raw_forecast, location_name)
        if processed:
            self.all_location_processed[loc_key] = processed
            self.loaded_locations.add(loc_key)
        else:
            self.loading_errors[loc_key] = "Failed to process forecast data"

    def _on_loading_complete(self, generation_id: int):
        """Handle completion of data loading."""
        if self._is_stale_generation(generation_id):
            return
        self.progress_var.set(PROGRESS_COMPLETE_PERCENT)
        loaded_count = len(self.loaded_locations)
        error_count = len(self.loading_errors)
        if loaded_count > 0:
            self._handle_successful_loading(loaded_count, error_count)
        else:
            self._handle_failed_loading(error_count)
        self.root.after(PROGRESS_HIDE_DELAY_MS, self.progress_bar.grid_remove)

    def _handle_successful_loading(self, loaded_count: int, error_count: int):
        """Update UI after at least one location loaded."""
        failed_text = f" ({error_count} failed)" if error_count > 0 else ""
        self._update_status(f"Loaded {loaded_count} locations successfully{failed_text}")
        self._populate_location_selector()
        self.subtitle_label.config(text=f"Weather data for {loaded_count} locations")

    def _handle_failed_loading(self, error_count: int):
        """Update UI after all location loading failed."""
        self._update_status("Failed to load any weather data")
        self.subtitle_label.config(text="No weather data available")
        if error_count == self.total_locations:
            messagebox.showerror(
                "Error",
                "Failed to load weather data. Please check your internet connection.",
            )

    def _update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.config(text=message)

    def _populate_location_selector(self):
        """Populate the location selector with loaded data."""
        if not self.loaded_locations:
            return
        location_names = self._loaded_location_names()
        self.location_dropdown["values"] = location_names
        if location_names:
            self.location_var.set(location_names[0])
            self.on_location_change()

    def _loaded_location_names(self) -> list[str]:
        """Return sorted names for successfully loaded locations."""
        names = [self.current_locations[loc_key].name for loc_key in self.loaded_locations]
        return sorted(names)

    def on_group_change(self, event=None):
        """Handle location group selection change."""
        try:
            group_name = self.group_var.get()
            if not group_name or group_name not in LOCATION_GROUPS:
                return
            self._switch_location_group(group_name)
            self._reset_group_state()
            self._reset_group_widgets()
            self._restart_group_loading()
            self._update_status(f"Switched to {group_name} locations")
        except Exception as e:
            self._update_status(f"Error changing region: {str(e)}")

    def _switch_location_group(self, group_name: str):
        """Switch the current location dictionary."""
        self.current_locations = LOCATION_GROUPS[group_name]
        self.total_locations = len(self.current_locations)

    def _reset_group_state(self):
        """Clear loaded data when changing location groups."""
        self.all_location_processed = {}
        self.loaded_locations = set()
        self.loading_errors = {}
        self.selected_location_key = ""
        self.selected_date = None
        self.date_map = {}

    def _reset_group_widgets(self):
        """Reset visible widgets when changing location groups."""
        self.location_var.set("")
        self.location_dropdown["values"] = []
        self.date_var.set("")
        self.date_dropdown["values"] = []
        self.main_table.delete(*self.main_table.get_children())
        self._clear_side_panel_entries()

    def _clear_side_panel_entries(self):
        """Clear all reusable side-panel labels."""
        for rank_label, name_label, score_label, details_label in self.side_panel_entries:
            rank_label.config(text="")
            name_label.config(text="")
            score_label.config(text="")
            details_label.config(text="")

    def _restart_group_loading(self):
        """Show loading UI and start fetching the selected group."""
        self.progress_bar.grid()
        self.subtitle_label.config(text="Loading weather data...")
        self._start_data_loading()

    def on_location_change(self, event=None):
        """Handle location selection change."""
        try:
            selected_name = self.location_var.get()
            if not selected_name:
                return
            self.selected_location_key = self._location_key_for_name(selected_name)
            if not self.selected_location_key:
                self._update_status(f"Location '{selected_name}' not found")
                return
            previous_date = self.selected_date
            self._populate_date_selector()
            self._restore_previous_date(previous_date)
            self._update_displays()
            self._update_status(f"Selected {selected_name}")
        except Exception as e:
            self._update_status(f"Error changing location: {str(e)}")

    def _location_key_for_name(self, selected_name: str) -> str:
        """Return the location key matching a display name."""
        return next(
            (key for key, loc in self.current_locations.items() if loc.name == selected_name),
            "",
        )

    def _restore_previous_date(self, previous_date):
        """Restore previous date selection if it exists for the new location."""
        if not previous_date or previous_date not in self.date_map.values():
            return
        date_str = self._date_string_for_value(previous_date)
        if date_str:
            self.date_var.set(date_str)
            self.selected_date = previous_date

    def _date_string_for_value(self, selected_date):
        """Return the selector string for a date value."""
        return next(
            (date_str for date_str, date_obj in self.date_map.items() if date_obj == selected_date),
            None,
        )

    def _populate_date_selector(self):
        """Populate the date selector."""
        try:
            processed = self._selected_processed_forecast()
            available_dates = get_available_dates(processed) if processed else []
            if not available_dates:
                self._clear_date_selector()
                return
            self._set_available_dates(available_dates)
        except Exception as e:
            self._update_status(f"Error loading dates: {str(e)}")

    def _selected_processed_forecast(self):
        """Return processed forecast data for the selected location."""
        if not self.selected_location_key:
            return None
        return self.all_location_processed.get(self.selected_location_key)

    def _clear_date_selector(self):
        """Clear date selector values and map."""
        self.date_dropdown["values"] = []
        self.date_map = {}

    def _set_available_dates(self, available_dates: list[date]):
        """Populate date selector with available forecast dates."""
        self.date_map = {format_date(d): d for d in available_dates}
        date_strings = list(self.date_map.keys())
        self.date_dropdown["values"] = date_strings
        if date_strings:
            self.date_var.set(date_strings[0])
            self.on_date_change()

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

    def on_activity_change(self, event=None):
        """Handle activity profile selection change."""
        try:
            selected_label = self.activity_profile_var.get()
            self.selected_activity_profile = get_activity_profile_key(selected_label)
            self.side_panel_title_label.config(text=self._get_side_panel_title())
            self._update_displays()
            self._update_status(f"Ranking for {selected_label}")

        except Exception as e:
            self._update_status(f"Error changing activity: {str(e)}")

    def _update_displays(self):
        """Update both side panel and main table."""
        try:
            self._update_side_panel()
            self._update_main_table()
        except Exception as e:
            self._update_status(f"Error updating displays: {str(e)}")

    def _get_side_panel_title(self) -> str:
        """Return the current side panel title."""
        activity_label = get_activity_profile_label(self.selected_activity_profile)
        return f"Top 10 for {activity_label}"

    def _update_side_panel(self):
        """Update the side panel."""
        self._clear_side_panel_entries()
        if not self.selected_date:
            return
        try:
            top_locations = self._top_locations_for_selected_date()
            self._populate_side_panel_entries(top_locations)
        except Exception as e:
            self._update_status(f"Error updating side panel: {str(e)}")

    def _top_locations_for_selected_date(self) -> list[dict]:
        """Return ranked locations for the selected date."""
        return get_top_locations_for_date(
            self.all_location_processed,
            self.selected_date,
            top_n=MAX_SIDE_PANEL_LOCATIONS,
            activity_profile=self.selected_activity_profile,
        )

    def _populate_side_panel_entries(self, top_locations: list[dict]):
        """Populate reusable side-panel rows from ranked locations."""
        for index, labels in enumerate(self.side_panel_entries):
            if index < len(top_locations):
                self._populate_location_entry(index + 1, top_locations[index], *labels)

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
        score_text, color = self._format_location_score(loc_data)
        score_label.config(text=score_text, foreground=color)
        details_label.config(text=self._format_location_details(loc_data))

    def _format_location_score(self, loc_data: Dict[str, Any]) -> tuple[str, str]:
        """Return formatted score text and rating color for a location row."""
        total_score = loc_data.get("raw_score", loc_data.get("avg_score", 0))
        activity_profile = loc_data.get(
            "activity_profile",
            self.selected_activity_profile,
        )
        rating = get_rating_info(total_score, activity_profile)
        normalized = normalize_score(total_score, activity_profile)
        activity_label = f"{get_activity_profile_label(activity_profile)} day"
        score_text = self._score_text(activity_label, normalized, total_score, rating)
        return score_text, get_rating_color(rating)

    def _score_text(
        self, activity_label: str, normalized: int, total_score: Any, rating: str
    ) -> str:
        """Return score text according to score-visibility settings."""
        score_text = f"{activity_label}: {normalized}/100"
        if self.show_scores.get():
            return score_text + f" (Raw: {total_score:.1f}, {rating})"
        return score_text + f" ({rating})"

    def _format_location_details(self, loc_data: Dict[str, Any]) -> str:
        """Return side-panel detail text for one location."""
        best_block = loc_data.get("optimal_block")
        if not best_block:
            return "No optimal block found"
        return self._format_block_details(best_block)

    def _format_block_details(self, best_block: dict[str, Any]) -> str:
        """Return details text for a recommended block."""
        start_str = format_time(best_block["start"])
        end_str = format_time(best_block["end"] + timedelta(hours=1))
        detail_lines = [
            f"Best time: {start_str} - {end_str}",
            f"Temp: {format_temperature(best_block.get('temp'))}",
            f"Wind: {format_wind_speed(best_block.get('wind'))}",
            f"Clouds: {format_percentage(best_block.get('cloud'))}",
            f"Rain: {format_precipitation(best_block.get('precip'))}",
            f"Rain risk: {format_percentage(best_block.get('precip_probability'))}",
            self._build_block_reason(best_block),
        ]
        return "\n".join(detail_lines)

    def _update_main_table(self):
        """Update the main table with data for the selected location."""
        self.main_table.delete(*self.main_table.get_children())
        if not self.selected_location_key or not self.selected_date:
            return
        try:
            processed = self._selected_processed_forecast()
            if not processed:
                return
            time_blocks = get_time_blocks_for_date(processed, self.selected_date)
            for block in time_blocks:
                self._insert_hourly_table_row(block)
        except Exception as e:
            self._update_status(f"Error updating table: {str(e)}")

    def _insert_hourly_table_row(self, block: Any):
        """Insert one hourly weather row."""
        self.main_table.insert(
            "",
            "end",
            values=self._hourly_row_values(block),
            tags=(self._rating_tag_for_block(block),),
        )

    def _hourly_row_values(self, block: Any) -> tuple[str, ...]:
        """Return formatted hourly table values."""
        return (
            format_time(block.time),
            format_temperature(block.temp),
            format_wind_speed(block.wind),
            format_percentage(block.cloud_coverage),
            format_precipitation(block.precipitation_amount),
            format_percentage(block.precipitation_probability),
            format_percentage(block.relative_humidity),
            self._format_profile_score(block),
        )

    def _rating_tag_for_block(self, block: Any) -> str:
        """Return the Treeview color tag for a weather row."""
        score = get_activity_score(block, self.selected_activity_profile)
        rating = get_rating_info(score, self.selected_activity_profile)
        return rating.replace(" ", "")

    def _format_profile_score(self, block: Any) -> str:
        """Format the selected activity score for the hourly table."""
        score = get_activity_score(block, self.selected_activity_profile)
        normalized = normalize_score(score, self.selected_activity_profile)
        if self.show_scores.get():
            rating = get_rating_info(score, self.selected_activity_profile)
            return f"{normalized}/100 ({score:.1f}, {rating})"
        return f"{normalized}/100"

    def _build_block_reason(self, best_block: dict[str, Any]) -> str:
        """Build a short human-readable reason for a recommended block."""
        warnings = self._block_warnings(best_block)
        positives = self._block_positives(best_block)
        if warnings:
            return self._reason_text("Watch", warnings)
        if positives:
            return self._reason_text("Why", positives)
        return "Why: steady conditions"

    def _block_warnings(self, best_block: dict[str, Any]) -> list[str]:
        """Return warning phrases for a recommended block."""
        warnings = self._rain_warnings(best_block)
        symbols = best_block.get("symbols", [])
        if symbols and any("thunder" in symbol for symbol in symbols):
            warnings.append("storm risk")
        if self._is_windy_beach_block(best_block):
            warnings.append("windy for swimming")
        return warnings

    def _rain_warnings(self, best_block: dict[str, Any]) -> list[str]:
        """Return rain-related warning phrases."""
        warnings = []
        if self._meets_threshold(best_block.get("precip_probability"), RAIN_RISK_WARNING_PERCENT):
            warnings.append("rain risk")
        if self._meets_threshold(best_block.get("precip"), RAIN_AMOUNT_WARNING_MM):
            warnings.append("wet spell")
        return warnings

    def _block_positives(self, best_block: dict[str, Any]) -> list[str]:
        """Return positive phrases for a recommended block."""
        positives = self._profile_positives(best_block)
        if self._is_dry_block(best_block):
            positives.append("dry")
        return positives

    def _profile_positives(self, best_block: dict[str, Any]) -> list[str]:
        """Return profile-specific positive phrases."""
        profile = best_block.get("activity_profile", self.selected_activity_profile)
        if profile == ACTIVITY_BEACH_DAY:
            return self._beach_positives(best_block)
        return self._hiking_positives(best_block)

    def _beach_positives(self, best_block: dict[str, Any]) -> list[str]:
        """Return beach-specific positive phrases."""
        positives = []
        if self._at_or_below(best_block.get("wind"), BEACH_CALM_WIND_SPEED):
            positives.append("calm")
        if self._at_or_below(best_block.get("cloud"), BEACH_GOOD_SUN_CLOUD_PERCENT):
            positives.append("good sun")
        return positives

    def _hiking_positives(self, best_block: dict[str, Any]) -> list[str]:
        """Return hiking-specific positive phrases."""
        positives = []
        if self._at_or_below(best_block.get("wind"), HIKING_COMFORTABLE_WIND_SPEED):
            positives.append("comfortable wind")
        if self._at_or_below(best_block.get("cloud"), HIKING_USABLE_LIGHT_CLOUD_PERCENT):
            positives.append("usable light")
        return positives

    def _is_windy_beach_block(self, best_block: dict[str, Any]) -> bool:
        """Return True when beach wind deserves a warning."""
        profile = best_block.get("activity_profile", self.selected_activity_profile)
        return profile == ACTIVITY_BEACH_DAY and self._meets_threshold(
            best_block.get("wind"), BEACH_WIND_WARNING_SPEED
        )

    def _is_dry_block(self, best_block: dict[str, Any]) -> bool:
        """Return True when a block is dry enough to mention."""
        rain = best_block.get("precip")
        rain_risk = best_block.get("precip_probability")
        return rain is not None and rain < DRY_RAIN_AMOUNT_MM and (
            rain_risk is None or rain_risk < DRY_RAIN_RISK_PERCENT
        )

    def _meets_threshold(self, value: Any, threshold: float) -> bool:
        """Return True when a numeric value is at least a threshold."""
        return value is not None and value >= threshold

    def _at_or_below(self, value: Any, threshold: float) -> bool:
        """Return True when a numeric value is at or below a threshold."""
        return value is not None and value <= threshold

    def _reason_text(self, prefix: str, phrases: list[str]) -> str:
        """Return a deduplicated reason sentence."""
        return f"{prefix}: " + ", ".join(dict.fromkeys(phrases))


def main():
    """Application entry point."""
    try:
        app = WeatherHelperApp()
        app.root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"An unexpected error occurred: {str(e)}")
