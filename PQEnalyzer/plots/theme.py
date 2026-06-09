"""
Matplotlib theme helpers aligned with CustomTkinter appearance modes.
"""

import customtkinter as ctk
import matplotlib
from cycler import cycler


LIGHT_PALETTE = {
    "figure.facecolor": "#f8fafc",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#64748b",
    "axes.labelcolor": "#0f172a",
    "text.color": "#0f172a",
    "tick.color": "#334155",
    "grid.color": "#cbd5e1",
    "legend.facecolor": "#ffffff",
    "legend.edgecolor": "#cbd5e1",
    "annotation.facecolor": "#f1f5f9",
    "annotation.edgecolor": "#cbd5e1",
    "colors": ["#2563eb", "#e11d48", "#059669", "#7c3aed", "#d97706"],
}

DARK_PALETTE = {
    "figure.facecolor": "#111827",
    "axes.facecolor": "#0f172a",
    "axes.edgecolor": "#94a3b8",
    "axes.labelcolor": "#e5e7eb",
    "text.color": "#e5e7eb",
    "tick.color": "#cbd5e1",
    "grid.color": "#334155",
    "legend.facecolor": "#111827",
    "legend.edgecolor": "#475569",
    "annotation.facecolor": "#1e293b",
    "annotation.edgecolor": "#475569",
    "colors": ["#60a5fa", "#fb7185", "#34d399", "#c084fc", "#fbbf24"],
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


def apply_matplotlib_theme(appearance_mode=None):
    """
    Apply a CustomTkinter-aligned palette to matplotlib defaults.
    """

    palette = palette_for_appearance_mode(appearance_mode)

    matplotlib.rcParams.update({
        "figure.facecolor": palette["figure.facecolor"],
        "axes.facecolor": palette["axes.facecolor"],
        "axes.edgecolor": palette["axes.edgecolor"],
        "axes.labelcolor": palette["axes.labelcolor"],
        "axes.grid": True,
        "axes.prop_cycle": cycler(color=palette["colors"]),
        "text.color": palette["text.color"],
        "xtick.color": palette["tick.color"],
        "ytick.color": palette["tick.color"],
        "grid.color": palette["grid.color"],
        "grid.alpha": 0.35,
        "legend.facecolor": palette["legend.facecolor"],
        "legend.edgecolor": palette["legend.edgecolor"],
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
    axes.grid(True, color=palette["grid.color"], alpha=0.35)
    axes.tick_params(colors=palette["tick.color"])
    axes.xaxis.label.set_color(palette["axes.labelcolor"])
    axes.yaxis.label.set_color(palette["axes.labelcolor"])
    axes.title.set_color(palette["text.color"])

    for spine in axes.spines.values():
        spine.set_color(palette["axes.edgecolor"])

    legend = axes.get_legend()
    if legend is not None:
        legend.get_frame().set_facecolor(palette["legend.facecolor"])
        legend.get_frame().set_edgecolor(palette["legend.edgecolor"])
        legend.get_frame().set_alpha(0.95)
        for text in legend.get_texts():
            text.set_color(palette["text.color"])

    for text in axes.texts:
        text.set_color(palette["text.color"])
        bbox = text.get_bbox_patch()
        if bbox is not None:
            bbox.set_facecolor(palette["annotation.facecolor"])
            bbox.set_edgecolor(palette["annotation.edgecolor"])
            bbox.set_alpha(0.85)

    return palette
