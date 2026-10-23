# AGENTS.md

## Commands
The dependencies are managed with [uv](https://docs.astral.sh/uv/).
- Install dependencies: `./install_requirements.sh`
  - This wraps `uv sync` and clears the Numba cache of PTtools when PTtools is updated.
- Run tests: `uv run pytest`
- Lint: `uv run ruff check`
- Type checking: `uv run pyrefly check`
- Run all lints and type checks: `./lint.sh`
  - This runs `pyrefly check`, `pyrefly coverage check`, `ruff check` and `python -m pttools.docs.lint`.
    All checks are run even if some of them fail. The exit code is 0 if all checks pass,
    the exit code of the failed check if exactly one check fails, and 100 if multiple checks fail.
  - Fast lint: `./lint.sh --fast` skips the significantly slower `python -m pttools.docs.lint`.
  - After changes that create or modify any reST or math markup in docstrings or `.rst` files, or files in `./docs/`, run the full lint `./lint.sh` (~2 min).
    After other changes, run the fast lint `./lint.sh --fast`.
- Build documentation with examples: `uv run make -C docs all`
  - This will run the examples and can therefore take 1-3 h.
- Build documentation without examples: `uv run make -C docs all-noplot`
- Update PTtools to the latest commit of its `dev` branch: `./install_requirements.sh --update-pttools`
  - This updates the `rev` of `pttools-gw` in `[tool.uv.sources]` in `./pyproject.toml` before installing.
    It also cleans the Numba cache of PTtools to ensure that cached functions from the previous version are removed.
  - To use a different commit, update the `rev` manually and run `./install_requirements.sh`.
- Update the other dependencies: `uv lock --upgrade`, or `uv lock --upgrade-package NAME` for a single one.
- Nightly run: `./ptplot/nightly.py --run` runs the unit tests, builds the documentation with examples and archives the results.
  It is run by cron.
  - Check the status of the nightly run with `./ptplot/nightly.py --status`, or `ptplot/nightly.py` without arguments.
    It prints the crontab entry, the schedule and the next run time, the current time,
    whether a nightly run is currently in progress, and the last lines of the latest log `./logs/nightly_YYYY-MM-DD.log`.
  - A nightly run in progress and all its child processes can be stopped with `./ptplot/nightly.py --stop`,
    and the next nightly run can be skipped with `./ptplot/nightly.py --skip`.
    The skip is consumed by the next `--run`, and it can be cancelled by deleting `./nightly.skip`.
  - If you're given an overnight task (e.g. "you have time until ..."),
    run `./ptplot/nightly.py --status` before starting to work on it.
    Skip the nightly run if needed. If you skip it, run it manually when you're done with your work.

## CI
- The CI and deploy workflows use reusable workflows and composite actions from the `dev` branch of PTtools,
  and have the same job structure as those of PTtools.
  The Docker image is published for every commit that passes the tests,
  and the PyPI package and the Software Heritage archive only for version tags, after all the other jobs have passed.
  Changes to the shared parts have to be made in the PTtools repository (`../pttools/.github`).

## Code style
- Use Python 3.12+ type hints where possible.
- JIT compile heavy computations with Numba.
- Prefer to organize modules alphabetically (ignoring the leading underscores)
  with constants first, then classes, and then functions.
  However, the exceptions are that `logger` should be right after the imports, and that `main` should be the last function in a module.
  You may deviate from these if required for e.g. type hints.

## Docstring conventions
- Use the Sphinx docstring format.
- Use `:param:`, `:return:` and `:raises:`, where appropriate.
  The descriptions of physics variables should begin with the form `$symbol$, name`, where appropriate.
- For functions that return a physics variable,
  the first line of the docstring should be of the form `$symbol$, name.`, where appropriate.
- If a function contains physics equations, add them as LaTeX in its docstring.
- When using equations from articles, cite the article, including the number of the equation, if possible.
- Use Sphinx extlinks for references.
- After changing equations in docstrings, run `uv run python -m pttools.docs.lint`.
  It builds the documentation without running the examples or generating the figures of the `plot` directive (`make latexpdf-noplot`), prints the Sphinx errors and warnings
  and the LaTeX errors, and saves the Sphinx output to `./logs/sphinx_TIMESTAMP.log`. Its exit code is that of `make`.
  It builds in a new temporary directory `./docs/lint/lint_TIMESTAMP_RANDOM`, whose path it prints,
  so multiple lints can be run simultaneously. These directories are not removed automatically.
  Fix all reported errors, as the documentation is built with `--fail-on-warning`.
- In docstring equations, write `\ast` instead of `*` after an opening bracket, e.g. `r_{\ast,0}`,
  as reStructuredText reads `{*` as the start of italics.

## General instructions
- PTtools is installed as a pip package to the uv-managed virtualenv, usually in `./.venv`.
  The examples and unit tests of PTtools may be available at `../pttools`.
- Before editing code that has physics equations, ensure that there are unit tests that verify the results of that code.
  If there are no such unit tests yet, create them. Use the existing output of the code as a reference,
  and also reference values from the literature, if there are any.
- If you change any of the physics, inform the user explicitly and exactly what has been changed.
- When changing the physics beyond bug fixes, add an argument for switching to the old behaviour, if feasible.

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

PTPlot supports five modeling engines:
- Broken power law (BPL) of Hindmarsh et al. (2017) and Caprini et al. (2020), `bpl-2020` (default)
- Broken power law (BPL) of Caprini et al. (2024), `bpl-2024`
- Double-broken power law (DBPL) of Gowling & Hindmarsh (2021), `dbpl-2021`
- Double-broken power law (DBPL) of Caprini et al. (2024), `dbpl-2024`
- Sound Shell Model (SSM), provided by the PTtools library from the same authors as PTPlot

## Related repositories
You may `git clone` these with SSH in the same parent directory as PTPlot.
- [PTtools](https://github.com/CFT-HY/pttools): `../pttools` (public)
  - PTPlot uses PTtools as a back-end for the Sound Shell Model and various utilities.
  - PTtools is maintained by the same authors as PTPlot. Therefore, if you need a feature or a change in PTtools,
    you may implement it in the local copy, if there are no uncommitted changes in the relevant files or other active sessions editing the code.
- Correia et al. (2025), "Gravitational waves from strong first-order phase transitions" (Correia:2025qif, 2505.17824)
  - [Hydro_plot](https://github.com/jrcccc/Hydro_plot): `../Hydro_plot`, another version of the plotting code (private)
  - [UETC_paper_Hydro](https://github.com/jrcccc/UETC_paper_Hydro): `../UETC_paper_Hydro`, the code and data used in the article (private)
