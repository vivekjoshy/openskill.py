"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import sys
from pathlib import Path

import openskill

source_path = str(Path("../..", "openskill").resolve())
sys.path.insert(0, source_path)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project: str = "openskill.py"
copyright: str = "Copyright &copy 2023 - 2025, Vivek Joshy"
author: str = "Vivek Joshy"
version: str = openskill.__version__
release: str = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions: list[str] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinxcontrib.bibtex",
    "sphinx_favicon",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "myst_parser",
    "nbsphinx",
    "sphinx_docsearch",
]

templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "OpenSkill: Multiplayer Rating System. No Friction."
html_theme = "shibuya"
html_static_path = ["_static"]
html_theme_options = {
    "dark_code": False,
    "github_url": "https://github.com/vivekjoshy/openskill.py",
    "discord_url": "https://discord.gg/4JNDeHMYkM",
    "light_logo": "_static/text_logo_light.svg",
    "dark_logo": "_static/text_logo_dark.svg",
}
html_context = {
    "source_type": "github",
    "source_user": "vivekjoshy",
    "source_repo": "openskill.py",
    "source_version": "main",
    "source_docs_path": "/docs/source/",
}

html_copy_source = False
html_show_sourcelink = False
template_path = ["_templates"]

# -- Options for AutoDoc output ----------------------------------------------
autodoc_typehints = "signature"
autodoc_preserve_defaults = True
autoclass_content = "both"  # Display __init__ parameter docs.

# -- Options for AutoSummary -------------------------------------------------
autosummary_generate = False
autosummary_imported_members = True

# -- Options for BibTeX output -----------------------------------------------
bibtex_bibfiles = ["./references.bib"]
bibtex_reference_style = "author_year"
bibtex_default_style = "alpha"

# -- Options for MathJax output ----------------------------------------------
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"

# -- Options for OpenGraph output ---------------------------------------------
ogp_site_url = "https://openskill.me/en/stable/"
ogp_site_name = "OpenSkill: Multiplayer Rating System. No Friction."
ogp_image = "https://i.imgur.com/HqkBLVt.png"
ogp_description_length = 200
ogp_type = "website"
ogp_enable_meta_description = True

# -- Options for Favicon output ----------------------------------------------
html_favicon = "_static/favicon.ico"
favicons = [
    {"href": "logo.svg"},
    {"href": "favicon-16x16.png"},
    {"href": "favicon-32x32.png"},
    {
        "rel": "apple-touch-icon",
        "href": "apple-touch-icon.png",
    },
    {
        "rel": "manifest",
        "href": "site.webmanifest",
    },
]

# Docsearch
docsearch_app_id = "TUWNQQ885H"
docsearch_api_key = "19a09d80f4b370188bea620ff3738fb1"
docsearch_index_name = "openskill"
nbsphinx_requirejs_path = ""
