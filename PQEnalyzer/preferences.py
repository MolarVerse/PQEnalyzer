"""
Persistent user preferences shared by the GUI and plot windows.
"""

import contextlib
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import sys

from ._logging import get_logger


logger = get_logger(__name__)

APPEARANCE_MODES = {"System", "Light", "Dark"}
PLOT_SCALE_PRESETS = (
    0.75,
    0.85,
    0.9,
    0.95,
    1.0,
    1.05,
    1.1,
    1.25,
    1.5,
    1.75,
    2.0,
)
PLOT_SCALE_LABELS = tuple(
    f"{scale:.0%}"
    for scale in PLOT_SCALE_PRESETS
)
DEFAULT_PLOT_SCALE = 1.0
PLOT_SIZE_KEYS = {"single", "dashboard"}


@dataclass
class UserPreferences:
    """
    Last user-selected GUI and plot settings.
    """

    appearance_mode: str = "System"
    plot_scale: float = DEFAULT_PLOT_SCALE
    plot_sizes: dict[str, tuple[float, float]] = field(default_factory=dict)
    selected_parameter: str | None = None
    auto_refresh: bool = True
    plot_options: dict = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, values):
        """
        Build validated preferences from decoded JSON-compatible data.
        """

        if not isinstance(values, dict):
            return cls()

        appearance_mode = values.get("appearance_mode")
        if appearance_mode not in APPEARANCE_MODES:
            appearance_mode = "System"

        selected_parameter = values.get("selected_parameter")
        if not isinstance(selected_parameter, str) or not selected_parameter:
            selected_parameter = None

        auto_refresh = values.get("auto_refresh")
        if not isinstance(auto_refresh, bool):
            auto_refresh = True

        plot_options = values.get("plot_options")
        if not isinstance(plot_options, dict):
            plot_options = {}

        plot_sizes = {}
        stored_plot_sizes = values.get("plot_sizes")
        if isinstance(stored_plot_sizes, dict):
            for key in PLOT_SIZE_KEYS:
                size = _validated_size(stored_plot_sizes.get(key))
                if size is not None:
                    plot_sizes[key] = size

        return cls(
            appearance_mode=appearance_mode,
            plot_scale=normalize_plot_scale(
                values.get("plot_scale", values.get("display_scale"))),
            plot_sizes=plot_sizes,
            selected_parameter=selected_parameter,
            auto_refresh=auto_refresh,
            plot_options=plot_options,
        )

    def to_mapping(self):
        """
        Return JSON-compatible preference data.
        """

        return {
            "appearance_mode": self.appearance_mode,
            "plot_scale": self.plot_scale,
            "plot_sizes": {
                key: list(size)
                for key, size in self.plot_sizes.items()
                if key in PLOT_SIZE_KEYS
            },
            "selected_parameter": self.selected_parameter,
            "auto_refresh": self.auto_refresh,
            "plot_options": self.plot_options,
        }


def normalize_plot_scale(value):
    """
    Return the nearest supported plot scale.
    """

    try:
        plot_scale = float(value)
    except (TypeError, ValueError):
        return DEFAULT_PLOT_SCALE

    if not math.isfinite(plot_scale):
        return DEFAULT_PLOT_SCALE

    return min(
        PLOT_SCALE_PRESETS,
        key=lambda preset: (abs(preset - plot_scale), preset),
    )


def adjusted_plot_scale(current_scale, action):
    """
    Return the neighboring preset for an increase, decrease, or reset.
    """

    if action == "reset":
        return DEFAULT_PLOT_SCALE

    normalized_scale = normalize_plot_scale(current_scale)
    current_index = PLOT_SCALE_PRESETS.index(normalized_scale)
    if action == "increase":
        target_index = min(current_index + 1, len(PLOT_SCALE_PRESETS) - 1)
    elif action == "decrease":
        target_index = max(current_index - 1, 0)
    else:
        raise ValueError(f"Unknown plot scale action: {action}")

    return PLOT_SCALE_PRESETS[target_index]


def plot_scale_label(plot_scale):
    """
    Return a percentage label for one supported plot scale.
    """

    return f"{normalize_plot_scale(plot_scale):.0%}"


def plot_scale_from_label(label):
    """
    Return the supported scale represented by a percentage label.
    """

    if not isinstance(label, str) or not label.endswith("%"):
        return DEFAULT_PLOT_SCALE

    try:
        value = float(label[:-1]) / 100
    except ValueError:
        return DEFAULT_PLOT_SCALE
    return normalize_plot_scale(value)


def plot_scale_action(key):
    """
    Map a Matplotlib key description to a plot-scale action.
    """

    normalized_key = (key or "").lower()
    if normalized_key in {
        "+",
        "=",
        "ctrl++",
        "ctrl+=",
        "cmd++",
        "cmd+=",
    }:
        return "increase"
    if normalized_key in {"-", "ctrl+-", "cmd+-"}:
        return "decrease"
    if normalized_key in {"0", "ctrl+0", "cmd+0"}:
        return "reset"
    return None


def preferences_path():
    """
    Return the platform-appropriate settings file path.
    """

    override = os.environ.get("PQENALYZER_CONFIG_DIR")
    if override:
        config_directory = Path(override).expanduser()
    elif sys.platform == "darwin":
        config_directory = (
            Path.home() / "Library" / "Application Support" / "PQEnalyzer"
        )
    elif sys.platform.startswith("win"):
        app_data = os.environ.get("APPDATA")
        config_directory = (
            Path(app_data)
            if app_data
            else Path.home() / "AppData" / "Roaming"
        ) / "PQEnalyzer"
    else:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        config_directory = (
            Path(config_home).expanduser()
            if config_home
            else Path.home() / ".config"
        ) / "pqenalyzer"

    return config_directory / "settings.json"


def load_preferences(path=None):
    """
    Load preferences, returning defaults for missing or invalid files.
    """

    settings_path = Path(path) if path is not None else preferences_path()
    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            values = json.load(settings_file)
    except FileNotFoundError:
        return UserPreferences()
    except (OSError, ValueError) as error:
        logger.warning("Could not read preferences from %s: %s",
                       settings_path, error)
        return UserPreferences()

    return UserPreferences.from_mapping(values)


def save_preferences(preferences, path=None):
    """
    Atomically save preferences and return whether the write succeeded.
    """

    settings_path = Path(path) if path is not None else preferences_path()
    temporary_path = settings_path.with_suffix(".tmp")
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as settings_file:
            json.dump(
                preferences.to_mapping(),
                settings_file,
                indent=2,
                sort_keys=True,
            )
            settings_file.write("\n")
        temporary_path.replace(settings_path)
    except OSError as error:
        with contextlib.suppress(OSError):
            temporary_path.unlink()
        logger.warning("Could not save preferences to %s: %s",
                       settings_path, error)
        return False

    return True


def _validated_size(value):
    """
    Return a positive two-dimensional size or ``None``.
    """

    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None

    try:
        width, height = (float(dimension) for dimension in value)
    except (TypeError, ValueError):
        return None

    if (
        not math.isfinite(width)
        or not math.isfinite(height)
        or width <= 0
        or height <= 0
    ):
        return None

    return round(width, 2), round(height, 2)
