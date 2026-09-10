"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

from datetime import date
import os.path
import sys
import tomllib

from pttools.docs.intersphinx import INTERSPHINX_MAPPING, IntersphinxMapping
from pttools.docs.links import EXTLINKS_DYNAMIC, EXTLINKS_STATIC, ExtLinks, convert_extlinks
from pttools.docs.setup import pre_setup, setup_sphinx
from sphinx_gallery.sorting import ExplicitOrder

DOCS_DIR: str = os.path.dirname(os.path.abspath(__file__))
REPO_DIR: str = os.path.dirname(DOCS_DIR)
EXAMPLES_DIR: str = os.path.join(REPO_DIR, "examples")
PTPLOT_SITE_DIR: str = os.path.join(REPO_DIR, "ptplot_site")
sys.path.insert(0, REPO_DIR)

from ptplot import PTPLOT_DIR  # noqa: E402
from ptplot.methods import setup_django  # noqa: E402

setup_django()
# This is required so that ptplot_site.settings.prod can be imported.
os.environ["DJANGO_SECRET_KEY"] = "SET_ME_IN_PRODUCION"

DOC_MODULES: tuple[str, ...] = ("docs", "examples", "ptplot", "ptplot_site")
pre_setup(doc_modules=DOC_MODULES)

# Create a directory for static files to avoid a warning when building.
os.makedirs(os.path.join(DOCS_DIR, "_static"), exist_ok=True)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PTPlot"
with open(os.path.join(REPO_DIR, "AUTHORS")) as file:
    _authors = file.read().splitlines()
author = f"{', '.join(_authors[:-1])} & {_authors[-1]}"
copyright = f"2018-{date.today().year}, {author}"
with open (os.path.join(REPO_DIR, "pyproject.toml"), "rb") as file:
    version = tomllib.load(file)["project"]["version"]
release = version


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

setup = setup_sphinx
extensions = [
    "matplotlib.sphinxext.plot_directive",
    # Automatic documentation for Python code
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
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

suppress_warnings = [
    # Automatic section labeling produces duplicated labels. This silences the warnings from those.
    # https://github.com/sphinx-doc/sphinx/issues/7728
    # https://github.com/sphinx-doc/sphinx/issues/7697
    "autosectionlabel.*",
]


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


# -- Apidoc  -----------------------------------------------------------------
apidoc_modules = [
    {
        "path": PTPLOT_DIR,
        "destination": "gen_modules/ptplot"
    },
    {
        "path": PTPLOT_SITE_DIR,
        "destination": "gen_modules/ptplot_site"
    },
    {
        # Only the utilities are documented, as the examples themselves are in the gallery,
        # and importing them for autodoc would run them a second time.
        "path": EXAMPLES_DIR,
        "destination": "gen_modules/examples",
        "exclude_patterns": [os.path.join(EXAMPLES_DIR, "*", "*")]
    },
    {
        # This file is excluded, since importing it for autodoc would run it a second time.
        # The figure scripts are excluded, as they are already included with the plot directive.
        "path": DOCS_DIR,
        "destination": "gen_modules/docs",
        "exclude_patterns": [os.path.join(DOCS_DIR, "conf.py"), os.path.join(DOCS_DIR, "fig")]
    }
]
# apidoc_max_depth = 6
apidoc_module_first = True
apidoc_separate_modules = True


# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
    # This would result in duplicate class descriptions when using a template.
    # "members": True,
    "show-inheritance": True,
    "undoc-members": True,
}
autoclass_content = "both"
autodoc_preserve_defaults = True
autodoc_typehints = "description"


# -- Other -------------------------------------------------------------------

# Sphinx requires base URLs and caption strings to contain exactly one "%s",
# and all other "%" need to be escaped as "%%".
# EXTLINKS_STATIC: ExtLinks = {
#     **EXTLINKS_STATIC,
#     # ...
# }
EXTLINKS_DYNAMIC: ExtLinks = {
    **EXTLINKS_DYNAMIC,
    # Other
    "hakkinen_ptplot": (
        "https://version.helsinki.fi/hakkijen/ptplot-with-pttools/%s",
        "PTPlot version by Jenni Häkkinen%s"
    )
}
extlinks: ExtLinks = {
    **convert_extlinks(EXTLINKS_STATIC),
    **EXTLINKS_DYNAMIC
}
intersphinx_mapping: IntersphinxMapping = {
    **INTERSPHINX_MAPPING,
    "django": ("https://docs.djangoproject.com/en/stable/", None),
    "dulwich": ("https://dulwich.readthedocs.io/en/latest/", None),
    "pttools": ("https://pttools.readthedocs.io/en/latest/", None),
}
linkcheck_ignore: list[str] = [
    "https://doi.org/10.1103/PhysRevD.101.089902",
    "https://medium.com/*"
]
linkcheck_retries = 5
# Timeout had to be increased from 5 to prevent errors with slow ArXiv links
linkcheck_timeout = 20
linkcheck_workers = 10

show_memory = True

sphinx_gallery_conf = {
    "backreferences_dir": "gen_modules/backreferences",
    "compress_images": ("images", "thumbnails"),
    "doc_module": DOC_MODULES,
    "examples_dirs": EXAMPLES_DIR,
    "filename_pattern": ".*",
    "gallery_dirs": "auto_examples",
    "ignore_pattern": r"(__init__\.py|utils\.py)",
    "image_srcset": ["2x"],
    # "line_numbers": True,
    "matplotlib_animations": (True, "mp4"),
    # Parallelism cannot be enabled simultaneously with "show_memory".
    # It may also produce errors with some IDEs:
    # https://stackoverflow.com/questions/31080829/python-error-io-unsupportedoperation-fileno
    "parallel": not show_memory,
    # This has to be set in order to avoid a warning when disabling it with a command line option.
    # https://sphinx-gallery.github.io/stable/configuration.html#building-without-executing-examples
    "plot_gallery": "True",
    # "prefer_full_module": ...
    # By default, Sphinx-Gallery refers to the objects by the shortest name with which they are accessible,
    # e.g. "pttools.models.BagModel", but Sphinx documents them by the module in which they are defined,
    # e.g. "pttools.models.bag.BagModel". Without this, the hyperlinks from the examples to the API documentation
    # cannot be resolved, and the backreferences, that the mini-galleries are based on, are stored under names
    # that don't correspond to the documented objects.
    "prefer_full_module": {rf"^{module}\." for module in DOC_MODULES},
    # The None values mean that the objects are documented in this documentation instead of an external one.
    "reference_url": dict.fromkeys(DOC_MODULES),
    # "run_stale_examples": True
    "show_api_usage": True,
    "show_memory": show_memory,
    "subsection_order": ExplicitOrder([
        "../examples/snr"
    ]),
}
autosummary_generate = True
