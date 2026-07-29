# AGENTS.md

## Commands
- Install dependencies: `./install_requirements.sh`
- Run tests: `pytest`
- Lint: `pylint`
- Type checking: `mypy`
- Build documentation: `cd docs && make all`

## Code style
- Use Python 3.12 type hints where possible
- JIT compile heavy computations with Numba

## General instructions
- When working on code that has physics equations, ensure that the equations are not changed.

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
