For developers
==============

Setting up the development environment
--------------------------------------
The dependencies are managed with `uv <https://docs.astral.sh/uv/>`_.
Install it with the `instructions of uv <https://docs.astral.sh/uv/getting-started/installation/>`_
and then run

.. code-block:: bash

  ./install_requirements.sh

This creates the virtualenv ``.venv``, installs the dependency versions that are pinned in ``uv.lock``,
and installs PTPlot itself in editable mode.
It also clears the Numba cache of PTtools when PTtools is updated,
since those cache files are not tracked by the package manager.

Git hooks are managed with `prek <https://github.com/j178/prek>`_ and configured in ``prek.toml``.
Enable them with ``uv run prek install``.
The pre-commit hooks run the same checks as the fast lint ``./lint.sh --fast``
(``pyrefly check``, ``pyrefly coverage check`` and ``ruff check``) in parallel on the staged changes,
and block the commit if any of them fails.
They also fix trailing whitespace, missing newlines at the end of files and mixed line endings,
check the syntax of JSON, TOML and YAML files,
and check for large files and for the consistency of shebangs and executable bits.

The commands of the development tools are then run with ``uv run``, e.g.

.. code-block:: bash

  uv run pytest
  uv run ruff check
  uv run pyrefly check
  uv run make -C docs all

PTtools is installed from a Git commit, which is pinned with the ``rev``
of ``pttools-gw`` in the ``[tool.uv.sources]`` section of ``pyproject.toml``.
To update PTtools to the latest commit of its ``dev`` branch, run

.. code-block:: bash

  ./install_requirements.sh --update-pttools

To use a different commit, edit the ``rev`` and run ``./install_requirements.sh``.
The other dependencies can be updated with ``uv lock --upgrade``.


Developing a new feature
------------------------
Create a new feature branch in the repo.
If you don't have permissions to create a branch in the repo,
you can either request the permissions or create a fork.


Developing a hotfix
-------------------
Small bugfixes and improvements can be done in a separate hotfix branch.
This branch should be merged to main without squashing.


Creating a new release
----------------------
Update the PTPlot version number in:

- CITATION.cff
- codemeta.json
- pyproject.toml

Then run ``uv lock`` to update the version number in ``uv.lock`` as well.

Finally, create a release on GitHub with a new version tag of the form ``vX.Y.Z``.
The push of the tag runs the CI workflow, which publishes the package to PyPI,
the Docker image to Docker Hub and the GitHub Container registry,
and the repository to the Software Heritage archive, once all the other CI jobs have passed.


Updating Python version requirements
------------------------------------
When updating the Python version requirements,
update the version numbers in:

- .github/workflows/\*.yml
- .python-version
- .readthedocs.yaml
- Dockerfile
- pyproject.toml


Nightly runs
------------
The nightly run of PTPlot is run by the script ``pttools/docs/nightly.py`` of PTtools,
which runs the nightly runs of PTtools and PTPlot in sequence.
It runs the unit tests, builds the documentation (which also runs the examples) and the wheel,
and archives the results with 7-Zip to ``./docs/nightly/nightly_YYYY-MM-DD.7z``.
The examples save their figures to ``./docs/nightly/fig/fig_YYYY-MM-DD`` instead of the default ``./examples/fig``.
The figure directory is set with the ``PTPLOT_FIG_DIR`` environment variable,
which can also be used to change the figure directory when running the examples or building the documentation manually.
The run logs to ``./logs/nightly_YYYY-MM-DD.log``.
For the details and the setup of the cron job, see the section "Nightly runs"
in the `developer documentation of PTtools <https://pttools.readthedocs.io/en/latest/dev.html>`_.
