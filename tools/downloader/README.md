PTPlot Downloader
=================

This is a simple tool for generating the plots for the paper
https://arxiv.org/abs/1910.13125

It also serves as a handy integration test for PTPlot, to see what (if
anything) has changed, and to regenerate the server cache.

It consists of a python script `remove_watermark.py` to remove
annotations from the SVG file (and an older version
`remove_watermark_old.py`), and the script `download_LISA_figures.sh`
to fetch the set of figures used in the above paper.

The watermarks are easily removed in the SVG file, and when the plots
PTPlot generates will in due course evolve away from the 2019
'official' paper as the equations used are improved. Therefore it was
felt there was no harm in including this code here in the public repo,
especially as it helps with testing.

Prerequisites
-------------

- Curl (to download files)
- Inkscape (to convert to PDF)
- Python (presumed python3) with the lxml package

Running
-------

Either make `download_LISA_figures.sh` executable and run it:

    chmod +x download_LISA_figures.sh
    ./download_LISA_figures.sh
	
Or run with bash:

    bash ./download_LISA_figures.sh
	
It will create a new directory `files-<today's date>` write all the
files in there.
