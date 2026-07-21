"""
Matplotlib theme helpers aligned with CustomTkinter appearance modes.
"""

import customtkinter as ctk
import matplotlib
from cycler import cycler

PLOT_FONT_SIZES = {
    "base": 12.0,
    "title": 16.0,
    "axis_label": 14.0,
    "tick": 12.0,
    "legend": 12.0,
}


LIGHT_PALETTE = {
    "figure.facecolor": "#f4f7fb",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#0f172a",
    "text.color": "#0f172a",
    "subtle.text": "#64748b",
    "tick.color": "#475569",
    "grid.color": "#e2e8f0",
    "legend.facecolor": "#ffffff",
    "legend.edgecolor": "#cbd5e1",
    "annotation.facecolor": "#f1f5f9",
    "annotation.edgecolor": "#cbd5e1",
    "selected.edgecolor": "#2563eb",
    "warning.color": "#b45309",
    "colors": [
        "#2563eb",
        "#e11d48",
        "#059669",
        "#7c3aed",
        "#d97706",
        "#0891b2",
        "#be123c",
        "#16a34a",
    ],
}

DARK_PALETTE = {
    "figure.facecolor": "#0b1120",
    "axes.facecolor": "#111827",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#e5e7eb",
    "text.color": "#e5e7eb",
    "subtle.text": "#94a3b8",
    "tick.color": "#cbd5e1",
    "grid.color": "#1e293b",
    "legend.facecolor": "#0f172a",
    "legend.edgecolor": "#475569",
    "annotation.facecolor": "#0f172a",
    "annotation.edgecolor": "#475569",
    "selected.edgecolor": "#60a5fa",
    "warning.color": "#fbbf24",
    "colors": [
        "#60a5fa",
        "#fb7185",
        "#34d399",
        "#c084fc",
        "#fbbf24",
        "#22d3ee",
        "#f43f5e",
        "#4ade80",
    ],
}


def resolve_appearance_mode(appearance_mode=None):
    """
    Resolve ``System`` and unset modes to the active CustomTkinter mode.
    """

    if appearance_mode in {None, "System"}:
        return ctk.get_appearance_mode()

    return appearance_mode


def palette_for_appearance_mode(appearance_mode=None):
    """
    Return the palette matching a CustomTkinter appearance mode.
    """

    resolved_mode = resolve_appearance_mode(appearance_mode)
    if resolved_mode == "Dark":
        return DARK_PALETTE

    return LIGHT_PALETTE


def series_color(index, appearance_mode=None):
    """
    Return the stable plot color assigned to one input-file index.
    """

    colors = palette_for_appearance_mode(appearance_mode)["colors"]
    return colors[index % len(colors)]


def series_rgb(index, appearance_mode=None):
    """
    Return one indexed series color as an RGB tuple for terminal plots.
    """

    color = series_color(index, appearance_mode).lstrip("#")
    return tuple(int(color[offset:offset + 2], 16) for offset in (0, 2, 4))


def apply_matplotlib_theme(appearance_mode=None):
    """
    Apply a CustomTkinter-aligned palette to matplotlib defaults.
    """

    palette = palette_for_appearance_mode(appearance_mode)

    matplotlib.rcParams.update({
        "font.size": PLOT_FONT_SIZES["base"],
        "figure.facecolor": palette["figure.facecolor"],
        "axes.facecolor": palette["axes.facecolor"],
        "axes.edgecolor": palette["axes.edgecolor"],
        "axes.labelcolor": palette["axes.labelcolor"],
        "axes.labelsize": PLOT_FONT_SIZES["axis_label"],
        "axes.grid": True,
        "axes.prop_cycle": cycler(color=palette["colors"]),
        "axes.titleweight": "semibold",
        "axes.titlesize": PLOT_FONT_SIZES["title"],
        "lines.linewidth": 1.45,
        "lines.solid_capstyle": "round",
        "text.color": palette["text.color"],
        "xtick.color": palette["tick.color"],
        "xtick.labelsize": PLOT_FONT_SIZES["tick"],
        "ytick.color": palette["tick.color"],
        "ytick.labelsize": PLOT_FONT_SIZES["tick"],
        "grid.color": palette["grid.color"],
        "grid.alpha": 0.55,
        "legend.facecolor": palette["legend.facecolor"],
        "legend.edgecolor": palette["legend.edgecolor"],
        "legend.fontsize": PLOT_FONT_SIZES["legend"],
        "legend.framealpha": 0.95,
        "savefig.facecolor": palette["figure.facecolor"],
    })

    return palette


def apply_figure_theme(figure, axes, appearance_mode=None):
    """
    Apply the active palette to an already-created figure and axes.
    """

    palette = apply_matplotlib_theme(appearance_mode)

    figure.patch.set_facecolor(palette["figure.facecolor"])
    axes.set_facecolor(palette["axes.facecolor"])
    axes.grid(True, color=palette["grid.color"], alpha=0.55, linewidth=0.8)
    axes.tick_params(
        colors=palette["tick.color"],
        labelsize=PLOT_FONT_SIZES["tick"],
    )
    axes.xaxis.label.set_color(palette["axes.labelcolor"])
    axes.xaxis.label.set_size(PLOT_FONT_SIZES["axis_label"])
    axes.yaxis.label.set_color(palette["axes.labelcolor"])
    axes.yaxis.label.set_size(PLOT_FONT_SIZES["axis_label"])
    for title in (
        axes.title,
        getattr(axes, "_left_title", None),
        getattr(axes, "_right_title", None),
    ):
        if title is not None:
            title.set_color(palette["text.color"])
            title.set_size(PLOT_FONT_SIZES["title"])

    for spine in axes.spines.values():
        spine.set_color(palette["axes.edgecolor"])
        spine.set_linewidth(1.0)

    legend = axes.get_legend()
    if legend is not None:
        legend.get_frame().set_facecolor(palette["legend.facecolor"])
        legend.get_frame().set_edgecolor(palette["legend.edgecolor"])
        legend.get_frame().set_alpha(0.95)
        for text in legend.get_texts():
            text.set_color(palette["text.color"])
            text.set_size(PLOT_FONT_SIZES["legend"])
        legend.get_title().set_size(PLOT_FONT_SIZES["legend"])

    for text in axes.texts:
        text.set_color(palette["text.color"])
        bbox = text.get_bbox_patch()
        if bbox is not None:
            bbox.set_facecolor(palette["annotation.facecolor"])
            bbox.set_edgecolor(palette["annotation.edgecolor"])
            bbox.set_alpha(0.85)

    return palette
