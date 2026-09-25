"""
LOCAL-ONLY preview: PQSetup flat-mono design language on PQEnalyzer.

Reversible: delete this file and revert the small
``PQ_FLAT_MONO`` branches in ``plots/theme.py``, ``apps/app_layout.py`` and
``apps/tui.py``.

``tokens.json`` in ``@molarverse/pq-design`` is the single source of truth.
This module loads it from the sibling PQSetup checkout when available and
falls back to the embedded copy below (same values, kept in sync by hand for
this local preview).

Enable the preview with::

    PQ_FLAT_MONO=1 pqenalyzer ...

Default behaviour (env var unset) is unchanged.
"""

import json
import os
from pathlib import Path

ENV_VAR = "PQ_FLAT_MONO"

# Sibling checkout: MolarVerse/PQSetup/frontend/packages/pq-design/tokens.json
_TOKENS_PATH = (
    Path(__file__).resolve().parents[2]
    / "PQSetup"
    / "frontend"
    / "packages"
    / "pq-design"
    / "tokens.json"
)

# Embedded fallback (copy of tokens.json at time of preview).
_EMBEDDED_TOKENS = {
    "name": "MolarVerse flat-mono",
    "font": {
        "mono": '"IBM Plex Mono", "JetBrains Mono", ui-monospace, '
        "SFMono-Regular, Menlo, Consolas, monospace"
    },
    "color": {
        "background": "#f4f4f4",
        "surface": "#ffffff",
        "surface-subtle": "#f4f4f4",
        "surface-blue": "#edf5ff",
        "ink": "#161616",
        "ink-soft": "#393939",
        "muted": "#6f6f6f",
        "border": "#e0e0e0",
        "border-strong": "#8d8d8d",
        "accent": "#0f62fe",
        "accent-dark": "#0043ce",
        "accent-soft": "#edf5ff",
        "success": "#198038",
        "success-soft": "#defbe6",
        "warning": "#8e6a00",
        "warning-soft": "#fcf4d6",
        "danger": "#da1e28",
        "danger-soft": "#fff1f1",
        "selected": "#393939",
        "focus": "#0f62fe",
    },
    "shape": {"radius": "0", "radius-sm": "0", "shadow": "none"},
    "code": {"number": "#6929c4", "switch": "#198038", "file": "#005d5d"},
}


def is_flat_mono_enabled() -> bool:
    """Return True when the local flat-mono preview is requested."""
    return os.environ.get(ENV_VAR, "").strip() in {"1", "true", "yes", "on"}


def load_tokens() -> dict:
    """Return flat-mono tokens, preferring the sibling PQSetup checkout."""
    try:
        if _TOKENS_PATH.is_file():
            return json.loads(_TOKENS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return dict(_EMBEDDED_TOKENS)


def tokens_path() -> Path:
    """Return the tokens.json path used by this preview (may not exist)."""
    return _TOKENS_PATH


# Matplotlib palette derived from the tokens: Gray-10 surfaces, ink text,
# accent series. Single-hue + code colours keep plots calm and mono.
FLAT_MONO_MPL_PALETTE = {
    "figure.facecolor": "#f4f4f4",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#e0e0e0",
    "axes.labelcolor": "#161616",
    "text.color": "#161616",
    "subtle.text": "#6f6f6f",
    "tick.color": "#393939",
    "grid.color": "#e0e0e0",
    "legend.facecolor": "#ffffff",
    "legend.edgecolor": "#e0e0e0",
    "annotation.facecolor": "#edf5ff",
    "annotation.edgecolor": "#e0e0e0",
    "selected.edgecolor": "#0f62fe",
    "warning.color": "#8e6a00",
    # Data order: accent first, then cool hues; muddy olive and alarm red
    # stay late so ordinary multi-file plots read calm.
    "colors": [
        "#0f62fe",
        "#005d5d",
        "#6929c4",
        "#198038",
        "#0043ce",
        "#393939",
        "#8e6a00",
        "#da1e28",
    ],
}

# CustomTkinter mapping: square corners, mono type, hairline borders.
# Applied in apps/app_layout.py only when PQ_FLAT_MONO=1.
FLAT_MONO_CTK = {
    "background": "#f4f4f4",
    "surface": "#ffffff",
    "surface_subtle": "#f4f4f4",
    "ink": "#161616",
    "ink_soft": "#393939",
    "muted": "#6f6f6f",
    "border": "#e0e0e0",
    "border_strong": "#8d8d8d",
    "accent": "#0f62fe",
    "accent_dark": "#0043ce",
    "accent_soft": "#edf5ff",
    "success": "#198038",
    "warning": "#8e6a00",
    "danger": "#da1e28",
    "corner_radius": 0,
    "border_width": 1,
    # First available family wins; CustomTkinter falls back silently.
    "mono_font": ("IBM Plex Mono", "JetBrains Mono", "Menlo", "Consolas"),
}

# Textual TUI: light Gray-10, square panels, accent selection.
# Swapped in apps/tui.py only when PQ_FLAT_MONO=1.
FLAT_MONO_TUI_CSS = """
Screen {
    background: #f4f4f4;
    color: #161616;
}

#status,
#detail-title,
#detail-stats,
#help,
#chart-title,
#chart-controls {
    border: solid #e0e0e0;
    padding: 0 1;
}

#status {
    height: 4;
    color: #393939;
    background: #ffffff;
}

#parameters {
    height: 1fr;
    border: solid #0f62fe;
    background: #ffffff;
}

#detail-title {
    height: 3;
    color: #161616;
    background: #ffffff;
    text-style: bold;
}

#trend {
    height: 1fr;
    border: solid #e0e0e0;
    background: #ffffff;
    padding: 1 1;
}

#detail-stats {
    height: 8;
    background: #ffffff;
}

#help {
    height: 7;
    color: #6f6f6f;
    background: #ffffff;
}

#chart-title {
    height: 3;
    color: #161616;
    background: #ffffff;
    text-style: bold;
}

#chart-canvas {
    height: 1fr;
    border: solid #0f62fe;
    background: #ffffff;
    padding: 0 0;
    overflow: hidden;
}

#chart-controls {
    height: 6;
    color: #393939;
    background: #ffffff;
}
"""

FLAT_MONO_TUI_STATUS_STYLES = {
    "label": "#6f6f6f",
    "value": "bold #161616",
    "accent": "bold #0f62fe",
    "ok": "bold #198038",
    "warning": "bold #8e6a00",
    "error": "bold #da1e28",
}


def apply_flat_mono_matplotlib_theme(plot_scale=1.0):
    """Apply the flat-mono palette to matplotlib defaults (local preview)."""
    import matplotlib
    from cycler import cycler

    from .plots.theme import PLOT_FONT_SIZES, scaled_font_size

    font_sizes = {
        name: scaled_font_size(size, plot_scale)
        for name, size in PLOT_FONT_SIZES.items()
    }
    palette = FLAT_MONO_MPL_PALETTE
    matplotlib.rcParams.update(
        {
            # Mono everywhere per the language (base 14px / 1.5 equivalent).
            "font.family": "monospace",
            "font.monospace": [
                "IBM Plex Mono",
                "JetBrains Mono",
                "Menlo",
                "Consolas",
                "DejaVu Sans Mono",
            ],
            "font.size": font_sizes["base"],
            "figure.facecolor": palette["figure.facecolor"],
            "axes.facecolor": palette["axes.facecolor"],
            "axes.edgecolor": palette["axes.edgecolor"],
            "axes.labelcolor": palette["axes.labelcolor"],
            "axes.labelsize": font_sizes["axis_label"],
            "axes.grid": True,
            "axes.prop_cycle": cycler(color=palette["colors"]),
            "axes.titleweight": "semibold",
            "axes.titlesize": font_sizes["title"],
            # Square, hairline, no shadow: thin solid lines, square caps.
            "lines.linewidth": 1.5,
            "lines.solid_capstyle": "butt",
            "lines.solid_joinstyle": "miter",
            "axes.linewidth": 1.0,
            "grid.linewidth": 0.8,
            "grid.linestyle": "-",
            "text.color": palette["text.color"],
            "xtick.color": palette["tick.color"],
            "xtick.labelsize": font_sizes["tick"],
            "ytick.color": palette["tick.color"],
            "ytick.labelsize": font_sizes["tick"],
            "grid.color": palette["grid.color"],
            "grid.alpha": 1.0,
            "legend.facecolor": palette["legend.facecolor"],
            "legend.edgecolor": palette["legend.edgecolor"],
            "legend.fontsize": font_sizes["legend"],
            "legend.framealpha": 1.0,
            "legend.fancybox": False,
            "legend.shadow": False,
            "figure.edgecolor": palette["figure.facecolor"],
            "savefig.facecolor": palette["figure.facecolor"],
            "savefig.edgecolor": palette["figure.facecolor"],
        }
    )
    return palette
