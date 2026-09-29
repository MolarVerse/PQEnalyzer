"""Matplotlib theme helpers using the pinned PQDesign flat mono tokens."""

from ..flat_mono import FLAT_MONO_MPL_PALETTE, apply_flat_mono_matplotlib_theme


PLOT_FONT_SIZES = {
    "base": 12.0,
    "title": 16.0,
    "axis_label": 14.0,
    "tick": 12.0,
    "legend": 12.0,
}


def palette_for_appearance_mode(appearance_mode=None):
    """Return the shared flat mono palette for all desktop plots."""

    return FLAT_MONO_MPL_PALETTE


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


def scaled_font_size(font_size, plot_scale=1.0):
    """
    Scale one plot font size with the shared plot preference.
    """

    return round(float(font_size) * float(plot_scale), 2)


def apply_matplotlib_theme(appearance_mode=None, plot_scale=1.0):
    """Apply the shared flat mono palette to matplotlib defaults."""

    return apply_flat_mono_matplotlib_theme(plot_scale)


def apply_figure_theme(
    figure,
    axes,
    appearance_mode=None,
    plot_scale=1.0,
):
    """
    Apply the active palette to an already-created figure and axes.
    """

    palette = apply_matplotlib_theme(appearance_mode, plot_scale)
    font_sizes = {
        name: scaled_font_size(size, plot_scale)
        for name, size in PLOT_FONT_SIZES.items()
    }

    figure.patch.set_facecolor(palette["figure.facecolor"])
    axes.set_facecolor(palette["axes.facecolor"])
    axes.grid(True, color=palette["grid.color"], alpha=0.55, linewidth=0.8)
    axes.tick_params(
        colors=palette["tick.color"],
        labelsize=font_sizes["tick"],
    )
    axes.xaxis.label.set_color(palette["axes.labelcolor"])
    axes.xaxis.label.set_size(font_sizes["axis_label"])
    axes.yaxis.label.set_color(palette["axes.labelcolor"])
    axes.yaxis.label.set_size(font_sizes["axis_label"])
    for title in (
        axes.title,
        getattr(axes, "_left_title", None),
        getattr(axes, "_right_title", None),
    ):
        if title is not None:
            title.set_color(palette["text.color"])
            title.set_size(font_sizes["title"])

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
            text.set_size(font_sizes["legend"])
        legend.get_title().set_size(font_sizes["legend"])

    for text in axes.texts:
        text.set_color(palette["text.color"])
        bbox = text.get_bbox_patch()
        if bbox is not None:
            bbox.set_facecolor(palette["annotation.facecolor"])
            bbox.set_edgecolor(palette["annotation.edgecolor"])
            bbox.set_alpha(0.85)

    return palette
