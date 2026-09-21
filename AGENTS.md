# AGENTS.md

## Commands
- Install dependencies: `./install_requirements.sh`
- Run tests: `pytest`
- Lint: `ruff check`
- Type checking: `pyrefly check`
- Build documentation: `cd docs && make all`
  - This will run the examples and can therefore take 1-3 h.
- Build documentation without examples: `cd docs && make all-noplot`
- Update PTtools: update the commit hash of `pttools-gw` in `./requirements.txt` and run `./install_requirements.sh`.

## Code style
- Use Python 3.12+ type hints where possible.
- JIT compile heavy computations with Numba.

## Docstring conventions
- Use the Sphinx docstring format.
- Use `:param:`, `:return:` and `:raises:`, where appropriate.
  The descriptions of physics variables should begin with the form `$symbol$, name`, where appropriate.
- For functions that return a physics variable,
  the first line of the docstring should be of the form `$symbol$, name.`, where appropriate.
- If a function contains physics equations, add them as LaTeX in its docstring.
- When using equations from articles, cite the article, including the number of the equation, if possible.
- Use Sphinx extlinks for references.
- After changing equations in docstrings, run `python -m pttools.docs.lint`.
  It builds the documentation without running the examples (`make latexpdf-noplot`), prints the Sphinx errors and warnings
  and the LaTeX errors, and saves the Sphinx output to `./logs/sphinx_TIMESTAMP.log`. Its exit code is that of `make`.
  Fix all reported errors, as the documentation is built with `--fail-on-warning`.

## General instructions
- PTtools is installed as a pip package, usually in `./venv`.
  The examples and unit tests of PTtools may be available at `../pttools`.
- Before editing code that has physics equations, ensure that there are unit tests that verify the results of that code.
  If there are no such unit tests yet, create them. Use the existing output of the code as a reference,
  and also reference values from the literature, if there are any.
- If you change any of the physics, inform the user explicitly and exactly what has been changed.

## Description of PTPlot
PTPlot is a plotting tool for visualizing the gravitational wave power
spectrum from first-order phase transitions.
PTPlot was first developed for the article
"Detecting gravitational waves from cosmological phase transitions with LISA: an update"
by Caprini et al. (2020), arXiv:1910.13125.
Links to other relevant articles are in `docs.conf.extlinks`.

Modules:
- `ptplot` is the Django app
- `ptplot.science` contains the scientific code, which doesn't require Django
- `ptplot_site` is the Django site
- `tools` contains external utilities

PTPlot supports three modeling engines:
- Broken power law (BPL)
- Double-broken power law (DBPL)
- Sound Shell Model (SSM), provided by the PTtools library from the same authors as PTPlot
