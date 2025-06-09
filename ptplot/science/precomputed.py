"""List of available sensitivity curves

This file contains a list of available sensitivity curves for LISA, with
possible mission duration and labels.
"""

import typing as tp

# This corresponds to one of the sensitivity curves (C1) used in 1512.06239
# AVAILABLE_SENSITIVITY_CURVES = ["Sens_L6A2M5N2P2D28.txt"]
# AVAILABLE_SENSITIVITY_CURVES_LITE = ["Sens_L6A2M5N2P2D28_Lite.txt"]
# AVAILABLE_LABELS = ["Cfgv1 L6A2M5N2P2D28"]

AVAILABLE_SENSITIVITY_CURVES: tp.List[str] = [
    "ScienceRequirements.txt",
    "ScienceRequirements.txt"
]
AVAILABLE_SENSITIVITY_CURVES_LITE: tp.List[str] = [
    "ScienceRequirementsLite.txt",
    "ScienceRequirementsLite.txt"
]

AVAILABLE_DURATIONS: tp.List[tp.Union[int, float]] = [3, 7]

AVAILABLE_LABELS: tp.List[str] = [
    "Science Requirements Document (3 years)",
    "Science Requirements Document (7 years)"
]
