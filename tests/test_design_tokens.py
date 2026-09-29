"""The desktop theme must use the packaged PQDesign token snapshot."""

import json
from importlib.resources import files

from PQEnalyzer.flat_mono import (
    COLORS,
    FLAT_MONO_CTK,
    FLAT_MONO_MPL_PALETTE,
    FLAT_MONO_TUI_CSS,
)


def test_desktop_theme_uses_packaged_tokens():
    tokens = json.loads(
        files("PQEnalyzer").joinpath("design", "tokens.json").read_text())
    assert FLAT_MONO_CTK["accent"] == tokens["color"]["accent"]
    assert FLAT_MONO_MPL_PALETTE["axes.facecolor"] == tokens["color"]["surface"]
    assert f"background: {COLORS['background']}" in FLAT_MONO_TUI_CSS
