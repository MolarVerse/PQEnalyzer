import json
from pathlib import Path

import pytest

from PQEnalyzer import preferences


def test_preferences_round_trip_valid_values():
    stored = {
        "appearance_mode": "Dark",
        "plot_scale": 1.5,
        "plot_sizes": {
            "single": [12.5, 8],
            "dashboard": [15, 9.5],
            "unknown": [1, 1],
        },
        "selected_parameter": "TEMPERATURE",
        "auto_refresh": False,
        "plot_options": {
            "mean": True,
            "window_size": "25",
        },
    }

    user_preferences = preferences.UserPreferences.from_mapping(stored)

    assert user_preferences.appearance_mode == "Dark"
    assert user_preferences.plot_scale == 1.5
    assert user_preferences.plot_sizes == {
        "single": (12.5, 8.0),
        "dashboard": (15.0, 9.5),
    }
    assert user_preferences.selected_parameter == "TEMPERATURE"
    assert user_preferences.auto_refresh is False
    assert user_preferences.plot_options["mean"] is True
    assert user_preferences.to_mapping() == {
        "appearance_mode": "Dark",
        "plot_scale": 1.5,
        "plot_sizes": {
            "single": [12.5, 8.0],
            "dashboard": [15.0, 9.5],
        },
        "selected_parameter": "TEMPERATURE",
        "auto_refresh": False,
        "plot_options": {
            "mean": True,
            "window_size": "25",
        },
    }


def test_preferences_replace_invalid_values_with_defaults():
    user_preferences = preferences.UserPreferences.from_mapping({
        "appearance_mode": "Sepia",
        "plot_scale": float("nan"),
        "plot_sizes": {
            "single": [-1, 8],
            "dashboard": "large",
        },
        "selected_parameter": "",
        "auto_refresh": "yes",
        "plot_options": [],
    })

    assert user_preferences == preferences.UserPreferences()
    assert preferences.UserPreferences.from_mapping(None) == (
        preferences.UserPreferences()
    )


def test_preferences_migrate_legacy_display_scale_without_gui_size():
    user_preferences = preferences.UserPreferences.from_mapping({
        "display_scale": 1.05,
        "gui_size": [900, 700],
    })

    assert user_preferences.plot_scale == 1.05
    assert "gui_size" not in user_preferences.to_mapping()


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 1.0),
        ("large", 1.0),
        (float("inf"), 1.0),
        (0.1, 0.75),
        (1.333, 1.25),
        (4, 2.0),
    ],
)
def test_normalize_plot_scale(value, expected):
    assert preferences.normalize_plot_scale(value) == expected


def test_adjusted_plot_scale_uses_exact_neighboring_presets():
    assert preferences.adjusted_plot_scale(0.95, "increase") == 1.0
    assert preferences.adjusted_plot_scale(1.0, "increase") == 1.05
    assert preferences.adjusted_plot_scale(1.05, "decrease") == 1.0
    assert preferences.adjusted_plot_scale(1.0, "decrease") == 0.95
    assert preferences.adjusted_plot_scale(2.0, "increase") == 2.0
    assert preferences.adjusted_plot_scale(1.7, "reset") == 1.0

    with pytest.raises(ValueError, match="Unknown plot scale action"):
        preferences.adjusted_plot_scale(1.0, "larger")


def test_plot_scale_labels_round_trip_supported_presets():
    assert preferences.plot_scale_label(0.95) == "95%"
    assert preferences.plot_scale_label(1.0) == "100%"
    assert preferences.plot_scale_label(1.05) == "105%"
    assert preferences.plot_scale_from_label("105%") == 1.05
    assert preferences.plot_scale_from_label("invalid") == 1.0
    assert preferences.plot_scale_from_label("large%") == 1.0


@pytest.mark.parametrize(
    "key, expected",
    [
        ("+", "increase"),
        ("=", "increase"),
        ("CTRL++", "increase"),
        ("cmd+=", "increase"),
        ("-", "decrease"),
        ("ctrl+-", "decrease"),
        ("0", "reset"),
        ("cmd+0", "reset"),
        ("x", None),
        (None, None),
    ],
)
def test_plot_scale_action(key, expected):
    assert preferences.plot_scale_action(key) == expected


def test_preferences_path_uses_override(monkeypatch, tmp_path):
    monkeypatch.setenv("PQENALYZER_CONFIG_DIR", str(tmp_path))

    assert preferences.preferences_path() == tmp_path / "settings.json"


def test_preferences_path_uses_macos_application_support(monkeypatch):
    monkeypatch.delenv("PQENALYZER_CONFIG_DIR", raising=False)
    monkeypatch.setattr(preferences.sys, "platform", "darwin")

    assert preferences.preferences_path() == (
        Path.home()
        / "Library"
        / "Application Support"
        / "PQEnalyzer"
        / "settings.json"
    )


def test_preferences_path_uses_windows_app_data(monkeypatch, tmp_path):
    monkeypatch.delenv("PQENALYZER_CONFIG_DIR", raising=False)
    monkeypatch.setattr(preferences.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert preferences.preferences_path() == (
        tmp_path / "PQEnalyzer" / "settings.json"
    )

    monkeypatch.delenv("APPDATA")
    assert preferences.preferences_path() == (
        Path.home()
        / "AppData"
        / "Roaming"
        / "PQEnalyzer"
        / "settings.json"
    )


def test_preferences_path_uses_xdg_or_linux_default(monkeypatch, tmp_path):
    monkeypatch.delenv("PQENALYZER_CONFIG_DIR", raising=False)
    monkeypatch.setattr(preferences.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert preferences.preferences_path() == (
        tmp_path / "pqenalyzer" / "settings.json"
    )

    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert preferences.preferences_path() == (
        Path.home() / ".config" / "pqenalyzer" / "settings.json"
    )


def test_save_and_load_preferences(tmp_path):
    settings_path = tmp_path / "nested" / "settings.json"
    expected = preferences.UserPreferences(
        appearance_mode="Light",
        plot_scale=1.25,
    )

    assert preferences.save_preferences(expected, settings_path) is True
    assert preferences.load_preferences(settings_path) == expected
    assert json.loads(settings_path.read_text(encoding="utf-8"))[
        "appearance_mode"
    ] == "Light"
    assert not settings_path.with_suffix(".tmp").exists()


def test_load_preferences_handles_missing_and_invalid_files(tmp_path, caplog):
    missing_path = tmp_path / "missing.json"
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")

    assert preferences.load_preferences(missing_path) == (
        preferences.UserPreferences()
    )
    assert preferences.load_preferences(invalid_path) == (
        preferences.UserPreferences()
    )
    assert "Could not read preferences" in caplog.text


def test_save_preferences_handles_unwritable_path(tmp_path, caplog):
    blocked_directory = tmp_path / "blocked"
    blocked_directory.write_text("not a directory", encoding="utf-8")

    assert preferences.save_preferences(
        preferences.UserPreferences(),
        blocked_directory / "settings.json",
    ) is False
    assert "Could not save preferences" in caplog.text


@pytest.mark.parametrize(
    "value",
    [
        None,
        [1],
        ["wide", 1],
        [float("inf"), 1],
        [0, 1],
    ],
)
def test_invalid_sizes_are_rejected(value):
    assert preferences._validated_size(value) is None
