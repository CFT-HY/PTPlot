#!/bin/bash

# 1 = 2hdm

mkdir -p files/

handleplot () {
    
    num=$1
    label=$2

    echo -n "Processing plot ID $num with label $label... "

    # could use eb-django.ptplot.org
    curl -s https://www.ptplot.org/ptplot/models/${num}/snr_alphabeta.svg > files/${label}_snr.svg
    ./clean2.py files/${label}_snr.svg files/${label}_snr_cleaned.svg
    inkscape $(pwd)/files/${label}_snr_cleaned.svg --export-filename=$(pwd)/files/${label}_snr.pdf

    curl -s https://www.ptplot.org/ptplot/models/${num}/snr.svg > files/${label}_snr_ubarf.svg
    ./clean2.py files/${label}_snr_ubarf.svg files/${label}_snr_ubarf_cleaned.svg
    inkscape $(pwd)/files/${label}_snr_ubarf_cleaned.svg --export-filename=$(pwd)/files/${label}_snr_ubarf.pdf

    
    # rm files/${label}_snr.svg files/${label}_snr_cleaned.svg

    echo "done"
}
    
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


handlesingle () {
    
    vw=0.9
    alpha=0.1
    BetaoverH=50
    MissionProfile=0
    Tstar=200
    gstar=100

    type=$1

    echo -n "Processing single point plot type $type... "

    echo "curl -s https://www.ptplot.org/ptplot/$type?vw=$vw\&alpha=$alpha\&BetaoverH=$BetaoverH\&MissionProfile=$MissionProfile\&Tstar=$Tstar\&gstar=$gstar > files/single_${type}.svg"
    curl -s https://www.ptplot.org/ptplot/$type?vw=$vw\&alpha=$alpha\&BetaoverH=$BetaoverH\&MissionProfile=$MissionProfile\&Tstar=$Tstar\&gstar=$gstar > files/single_${type}.svg
    ./clean2.py files/single_${type}.svg files/single_${type}_cleaned.svg
    inkscape $(pwd)/files/single_${type}_cleaned.svg --export-filename=$(pwd)/files/single_${type}.pdf
    
    echo "done"
}


handlesingle ps.svg
handlesingle snr.svg
handlesingle snr_alphabeta.svg
