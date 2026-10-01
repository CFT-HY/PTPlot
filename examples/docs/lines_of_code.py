"""
Lines of code
=============

Count the lines of code of the PTPlot repository and the PTPlot module with
`cloc <https://github.com/AlDanial/cloc>`_ using :py:mod:`pttools.docs.cloc`.
The files are grouped by directory with :py:func:`pttools.docs.cloc.cloc_compact` to keep the lines short.
Only the files tracked by Git are counted, and the files matching the patterns of ``.clocignore`` are excluded.
"""

from pathlib import Path

from pttools.docs.cloc import cloc_compact

from ptplot import PTPLOT_DIR

REPO_DIR: Path = PTPLOT_DIR.parent


def main() -> None:
    """Print the lines of code of the PTPlot repository and the PTPlot module."""
    print("Lines of code in the PTPlot repository")
    print(cloc_compact(REPO_DIR))
    print("Lines of code in the PTPlot module")
    print(cloc_compact(PTPLOT_DIR))


if __name__ == "__main__":
    main()
