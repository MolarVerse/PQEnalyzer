"""Flat mono desktop and terminal styling from the pinned PQDesign tokens."""

import json
from importlib.resources import files
from string import Template

TOKENS = json.loads(
    files("PQEnalyzer").joinpath("design", "tokens.json").read_text()
)
COLORS = TOKENS["color"]
CODE_COLORS = TOKENS["code"]

FLAT_MONO_MPL_PALETTE = {
    "figure.facecolor": COLORS["background"],
    "axes.facecolor": COLORS["surface"],
    "axes.edgecolor": COLORS["border"],
    "axes.labelcolor": COLORS["ink"],
    "text.color": COLORS["ink"],
    "subtle.text": COLORS["muted"],
    "tick.color": COLORS["ink-soft"],
    "grid.color": COLORS["border"],
    "legend.facecolor": COLORS["surface"],
    "legend.edgecolor": COLORS["border"],
    "annotation.facecolor": COLORS["surface-blue"],
    "annotation.edgecolor": COLORS["border"],
    "selected.edgecolor": COLORS["accent"],
    "warning.color": COLORS["warning"],
    # Data order: accent first, then cool hues; muddy olive and alarm red
    # stay late so ordinary multi-file plots read calm.
    "colors": [
        COLORS["accent"],
        CODE_COLORS["file"],
        CODE_COLORS["number"],
        CODE_COLORS["switch"],
        COLORS["accent-dark"],
        COLORS["ink-soft"],
        COLORS["warning"],
        COLORS["danger"],
    ],
}

# CustomTkinter mapping: square corners, mono type, hairline borders.
FLAT_MONO_CTK = {
    "background": COLORS["background"],
    "surface": COLORS["surface"],
    "surface_subtle": COLORS["surface-subtle"],
    "ink": COLORS["ink"],
    "ink_soft": COLORS["ink-soft"],
    "muted": COLORS["muted"],
    "border": COLORS["border"],
    "border_strong": COLORS["border-strong"],
    "accent": COLORS["accent"],
    "accent_dark": COLORS["accent-dark"],
    "accent_soft": COLORS["accent-soft"],
    "success": COLORS["success"],
    "warning": COLORS["warning"],
    "danger": COLORS["danger"],
    "corner_radius": int(TOKENS["shape"]["radius"]),
    "border_width": 1,
    # First available family wins; CustomTkinter falls back silently.
    "mono_font": tuple(
        family.strip().strip('"')
        for family in TOKENS["font"]["mono"].split(",")
        if family.strip().strip('"') not in {"ui-monospace", "monospace"}
    ),
}

# Textual TUI: light Gray-10, square panels, accent selection.
FLAT_MONO_TUI_CSS = Template("""
Screen {
    background: $background;
    color: $ink;
}

#status,
#detail-title,
#detail-stats,
#help,
#chart-title,
#chart-controls {
    border: solid $border;
    padding: 0 1;
}

#status {
    height: 4;
    color: $ink_soft;
    background: $surface;
}

#parameters {
    height: 1fr;
    border: solid $accent;
    background: $surface;
}

#detail-title {
    height: 3;
    color: $ink;
    background: $surface;
    text-style: bold;
}

#trend {
    height: 1fr;
    border: solid $border;
    background: $surface;
    padding: 1 1;
}

#detail-stats {
    height: 8;
    background: $surface;
}

#help {
    height: 7;
    color: $muted;
    background: $surface;
}

#chart-title {
    height: 3;
    color: $ink;
    background: $surface;
    text-style: bold;
}

#chart-canvas {
    height: 1fr;
    border: solid $accent;
    background: $surface;
    padding: 0 0;
    overflow: hidden;
}

#chart-controls {
    height: 6;
    color: $ink_soft;
    background: $surface;
}
""").substitute(**{key.replace("-", "_"): value for key, value in COLORS.items()})

FLAT_MONO_TUI_STATUS_STYLES = {
    "label": COLORS["muted"],
    "value": f"bold {COLORS['ink']}",
    "accent": f"bold {COLORS['accent']}",
    "ok": f"bold {COLORS['success']}",
    "warning": f"bold {COLORS['warning']}",
    "error": f"bold {COLORS['danger']}",
}


def apply_flat_mono_matplotlib_theme(plot_scale=1.0):
    """Apply the flat-mono palette to matplotlib defaults."""
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
            "font.monospace": [*FLAT_MONO_CTK["mono_font"], "DejaVu Sans Mono"],
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
