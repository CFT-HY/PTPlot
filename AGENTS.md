# AGENTS.md

## Commands
- Install dependencies: `./install_requirements.sh`
- Run tests: `pytest`
- Lint: `ruff check`
- Type checking: `pyrefly check`
- Build documentation: `cd docs && make all`

## Code style
- Use Python 3.12 type hints where possible
- JIT compile heavy computations with Numba

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

Modules:
- `ptplot` is the Django app
- `ptplot.science` contains the scientific code, which doesn't require Django
- `ptplot_site` is the Django site
- `tools` contains external utilities

PTPlot supports three modeling engines:
- Broken power law (BPL)
- Double-broken power law (DBPL)
- Sound Shell Model (SSM), provided by the PTtools library from the same authors as PTPlot
