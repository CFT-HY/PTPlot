# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import date
import os.path
import sys
import tomllib

from sphinx_gallery.sorting import ExplicitOrder

dir_path = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.dirname(dir_path)
sys.path.insert(0, os.path.dirname(dir_path))

# Create a directory for static files to avoid a warning when building.
os.makedirs(os.path.join(dir_path, "_static"), exist_ok=True)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PTPlot'
with open(os.path.join(repo_path, "AUTHORS")) as file:
    _authors = file.read().splitlines()
author = f"{', '.join(_authors[:-1])} & {_authors[-1]}"
copyright = f"2018-{date.today().year}, {author}"
with open (os.path.join(repo_path, "pyproject.toml"), "rb") as file:
    version = tomllib.load(file)["project"]["version"]
release = version


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "matplotlib.sphinxext.plot_directive",
    # Automatic documentation for Python code
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    # Automatic labeling for documentation sections
    "sphinx.ext.autosectionlabel",
    # External links
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    # Mathematics rendering
    "sphinx.ext.mathjax",
    "sphinx_gallery.gen_gallery",
    "sphinx_math_dollar",
    # Markdown support can be enabled by uncommenting the line below.
    # https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html#using-markdown-with-sphinx
    # "myst_parser"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Automatic section labeling produces duplicated labels. This silences the warnings from those.
# https://github.com/sphinx-doc/sphinx/issues/7728
# https://github.com/sphinx-doc/sphinx/issues/7697
# suppress_warnings = ["autosectionlabel.*"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']


# -- LaTeX -------------------------------------------------------------------

# For Unicode support
latex_engine = "xelatex"


# -- Math --------------------------------------------------------------------

# This may not work unless changed to "mathjax_config", but that gives warnings with MathJax 3
mathjax3_config = {
    'tex2jax': {
        'inlineMath': [["\\(", "\\)"]],
        'displayMath': [["\\[", "\\]"]],
    },
}


# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
    # This would result in duplicate class descriptions when using a template.
    # "members": True,
    "show-inheritance": True,
    "undoc-members": True,
}
autodoc_preserve_defaults = True
autodoc_typehints = "description"


# -- Other -------------------------------------------------------------------

show_memory = True

sphinx_gallery_conf = {
    "backreferences_dir": "gen_modules/backreferences",
    "compress_images": ("images", "thumbnails"),
    "doc_module": ("ptplot", ),
    "examples_dirs": os.path.join(os.path.dirname(dir_path), "examples"),
    "filename_pattern": ".*",
    "gallery_dirs": "auto_examples",
    "ignore_pattern": r"(__init__\.py|utils\.py|p_s_scan_dev\.py|standard_model|entropy|reverse)",
    # "image_srcset": ["2x"],
    # "line_numbers": True,
    "matplotlib_animations": True,
    # Parallelism cannot be enabled simultaneously with "show_memory".
    # It may also produce errors with some IDEs:
    # https://stackoverflow.com/questions/31080829/python-error-io-unsupportedoperation-fileno
    "parallel": not show_memory,
    # "prefer_full_module": ...
    "reference_url": {
        "pttools": None,
        "tests": None,
    },
    # "run_stale_examples": True
    "show_memory": show_memory,
    "subsection_order": ExplicitOrder([
        "../examples/basic",
        "../examples/const_cs",
        # "../examples/standard_model",
        "../examples/props",
        # "../examples/entropy",
        "../examples/solvers",
        "../examples/giese",
        # "../examples/reverse",
        # "*"
    ])
}
autosummary_generate = True
