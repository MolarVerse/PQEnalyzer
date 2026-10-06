"""Sphinx configuration for the PQEnalyzer manual."""

project = "PQEnalyzer"
author = "MolarVerse"
copyright = "2026, the PQEnalyzer authors"
extensions = ["myst_parser", "sphinx_copybutton", "sphinx.ext.mathjax"]
source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", ".DS_Store"]
myst_enable_extensions = ["dollarmath"]
myst_heading_anchors = 3
html_theme = "furo"
html_logo = "_static/pq-logo.png"
html_favicon = "_static/pq-logo.png"
html_title = project
html_static_path = ["_static"]
html_css_files = ["pq-tokens.css", "pq-docs.css"]
html_js_files = ["pq-docs.js"]
html_theme_options = {
    "source_repository": "https://github.com/MolarVerse/PQEnalyzer/",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_baseurl = "https://molarverse.github.io/PQEnalyzer/"
