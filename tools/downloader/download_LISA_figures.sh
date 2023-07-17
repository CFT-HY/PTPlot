#!/bin/bash

# Code for batch downloading PTPlot figures from a vanilla server
# installation and generating figures in line with the paper
# https://arxiv.org/abs/1910.13125
#
# This code uses:
# - curl to download files
# - inkscape to convert SVGs to PDFs
# - python with the lxml package


# Python interpreter to use (environment needs lxml package)
PYTHON=python3
# Cleaning tool to use
CLEANER=remove_watermark.py
# Where to put files
DEST=files-`date +%Y-%m-%d`
# Server to read from
HOST=https://www.ptplot.org


# Check we're not overwriting something
if [ -d $DEST ]
then
   echo "Destination directory already exists, not going to overwrite: $DEST"
   exit 1
fi

echo "Creating destination directory: $DEST"
mkdir -p $DEST


# handleplot ()
#
# Function for downloading a plot from the server
#
# Arguments:
# $1 - benchmark model ID, known given the vanilla setup has fixed model IDs
# $2 - label for the figure
#
# Writes the following files:
#
# $DEST/${label}_snr.svg (alpha-beta space SNR plot)
# $DEST/${label}_snr_cleaned.svg (same with watermark removed)
# $DEST/${label}_snr.pdf (same but as PDF)
#
# $DEST/${label}_snr_ubarf.svg (ubarf-rstar space SNR plot)
# $DEST/${label}_snr_ubarf_cleaned.svg (same with watermark removed)
# $DEST/${label}_snr_ubarf_cleaned.pdf (same but as PDF)
handleplot () {
    
    num=$1
    label=$2

    echo -n "Processing plot ID $num with label $label... "

    curl -s $HOST/ptplot/models/${num}/snr_alphabeta.svg > $DEST/${label}_snr.svg
    $PYTHON $CLEANER $DEST/${label}_snr.svg $DEST/${label}_snr_cleaned.svg
    # Inkscape needs an absolute directory path, hence $(pwd) here.
    inkscape $(pwd)/$DEST/${label}_snr_cleaned.svg --export-filename=$(pwd)/$DEST/${label}_snr.pdf

    curl -s $HOST/ptplot/models/${num}/snr.svg > $DEST/${label}_snr_ubarf.svg
    $PYTHON $CLEANER $DEST/${label}_snr_ubarf.svg $DEST/${label}_snr_ubarf_cleaned.svg
    # Again, inkscape needs an absolute path.
    inkscape $(pwd)/$DEST/${label}_snr_ubarf_cleaned.svg --export-filename=$(pwd)/$DEST/${label}_snr_ubarf.pdf


    # [Don't] clean up
    # rm $DEST/${label}_snr.svg $DEST/${label}_snr_cleaned.svg

    echo "done"
}


# Handle the plots given known database model IDs
handleplot 1 2hdm
handleplot 2 z2_singlet_portal
handleplot 3 two_singlet_scalars
handleplot 4 dark_photon
handleplot 5 gauged_lepton_number
handleplot 6 composite_higgs
handleplot 7 randall_sundrum
handleplot 8 eft
handleplot 9 susy
handleplot 10 singlet

# Handlesingle
#
# Function for downloading single-point plots
#
# The phase transition parameters are fixed inside the function
#
# Arguments:
# $1 - type of plot (ps, snr, snr_alphabeta)
# [the suffix svg is added, and this is passed directly to the server
# as part of the URL]
#
# Writes the following files:
#
# $DEST/single_${type}.svg (single point plot of requested type)
# $DEST/single_${type}_cleaned.svg (same but with watermark removed)
# $DEST/single_${type}.pdf (same but as PDF)
handlesingle () {
    
    vw=0.9
    alpha=0.1
    BetaoverH=50
    MissionProfile=0
    Tstar=200
    gstar=100

    type=$1

    echo -n "Processing single point plot type $type... "

    # echo "curl -s $HOST/ptplot/${type}.svg?vw=$vw\&alpha=$alpha\&BetaoverH=$BetaoverH\&MissionProfile=$MissionProfile\&Tstar=$Tstar\&gstar=$gstar > $DEST/single_${type}.svg"
    curl -s $HOST/ptplot/${type}.svg?vw=$vw\&alpha=$alpha\&BetaoverH=$BetaoverH\&MissionProfile=$MissionProfile\&Tstar=$Tstar\&gstar=$gstar > $DEST/single_${type}.svg
    $PYTHON $CLEANER $DEST/single_${type}.svg $DEST/single_${type}_cleaned.svg

    # As in handleplot(), inkscape needs an absolute directory path
    # for some reason
    inkscape $(pwd)/$DEST/single_${type}_cleaned.svg --export-filename=$(pwd)/$DEST/single_${type}.pdf
    
    echo "done"
}


handlesingle ps
handlesingle snr
handlesingle snr_alphabeta
