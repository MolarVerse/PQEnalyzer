import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

from PQEnalyzer.plots import theme


def test_system_appearance_mode_resolves_to_current_customtkinter_mode(
        monkeypatch):
    monkeypatch.setattr(theme.ctk, "get_appearance_mode", lambda: "Dark")

    assert theme.resolve_appearance_mode("System") == "Dark"


def test_apply_matplotlib_theme_sets_dark_defaults():
    with mpl.rc_context():
        palette = theme.apply_matplotlib_theme("Dark")

        assert mpl.rcParams["figure.facecolor"] == palette["figure.facecolor"]
        assert mpl.rcParams["axes.facecolor"] == palette["axes.facecolor"]
        assert mpl.rcParams["text.color"] == palette["text.color"]
        assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == palette[
            "colors"]
        assert mpl.rcParams["axes.titlesize"] == theme.PLOT_FONT_SIZES[
            "title"]
        assert mpl.rcParams["axes.labelsize"] == theme.PLOT_FONT_SIZES[
            "axis_label"]
        assert mpl.rcParams["xtick.labelsize"] == theme.PLOT_FONT_SIZES[
            "tick"]
        assert mpl.rcParams["legend.fontsize"] == theme.PLOT_FONT_SIZES[
            "legend"]


def test_series_colors_are_stable_by_file_index():
    assert theme.series_color(1, "Light") == theme.LIGHT_PALETTE["colors"][1]
    assert theme.series_color(9, "Light") == theme.LIGHT_PALETTE["colors"][1]
    assert theme.series_rgb(1, "Dark") == (251, 113, 133)


def test_apply_figure_theme_updates_existing_plot_elements():
    with mpl.rc_context():
        figure, axes = plt.subplots()
        axes.plot([1, 2], [3, 4], label="data")
        axes.set_xlabel("Simulation step")
        axes.set_ylabel("Energy")
        axes.set_title("Energy trace", loc="left")
        axes.text(
            2,
            4,
            "4.000e+00",
            bbox=dict(facecolor="white", edgecolor="white"),
        )
        axes.legend()

        palette = theme.apply_figure_theme(figure, axes, "Dark")

        assert figure.get_facecolor() == to_rgba(palette["figure.facecolor"])
        assert axes.get_facecolor() == to_rgba(palette["axes.facecolor"])
        assert axes.xaxis.label.get_color() == palette["axes.labelcolor"]
        assert axes.yaxis.label.get_color() == palette["axes.labelcolor"]
        assert axes.xaxis.label.get_size() == theme.PLOT_FONT_SIZES[
            "axis_label"]
        assert axes.yaxis.label.get_size() == theme.PLOT_FONT_SIZES[
            "axis_label"]
        assert axes.get_xticklabels()[0].get_size() == theme.PLOT_FONT_SIZES[
            "tick"]
        assert axes.get_title(loc="left") == "Energy trace"
        assert axes._left_title.get_color() == palette["text.color"]
        assert axes._left_title.get_size() == theme.PLOT_FONT_SIZES["title"]
        legend_text = axes.get_legend().get_texts()[0]
        assert legend_text.get_color() == palette["text.color"]
        assert legend_text.get_size() == theme.PLOT_FONT_SIZES["legend"]
        assert axes.texts[0].get_color() == palette["text.color"]
        assert axes.texts[0].get_bbox_patch().get_alpha() == 0.85
