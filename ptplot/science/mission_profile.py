"""List of available mission profiles (sensitivity curves).

This file contains a list of available sensitivity curves for LISA,
with possible mission duration and labels.
"""

import os.path

import numpy as np

from ptplot.science.const import YEAR_IN_SECONDS
import ptplot.science.type_hints as th

SENSITIVITY_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensitivity")


class MissionProfile:
    """Mission profile containing the sensitivity curve and related information."""

    def __init__(
            self,
            name: str,
            duration: int | float,
            sensitivity_path: str,
            sensitivity_path_lite: str,
            notes: str | None = None):
        self.name = name
        self.duration_years = duration
        self.sensitivity_path = sensitivity_path
        self.sensitivity_path_lite = sensitivity_path_lite
        self.notes = notes
        # This will be set immediately after instantiation
        self.ind: int = -1

        #: Frequencies $f$ corresponding to the sensitivity values
        self.f: th.FloatArr1D
        #: Sensitivities $\Omega_\text{sens}$
        self.sensitivity: th.FloatArr1D

        self.f, self.sensitivity = self.load(self.sensitivity_path)
        self.f_lite, self.sensitivity_lite = self.load(self.sensitivity_path_lite)
        self.f_min = np.min(self.f)
        self.f_max = np.max(self.f)

    def __str__(self):
        return self.name

    @staticmethod
    def from_ind(index: int | None = None) -> "MissionProfile":
        return DEFAULT_MISSION_PROFILE if index is None else MISSION_PROFILES[index]

    @staticmethod
    def load(path: str) -> th.FloatArr2D:
        if not os.path.isabs(path):
            path = os.path.join(SENSITIVITY_ROOT, path)
        # The output must be C-contiguous, so that f and sensitivity are each contiguous.
        return np.ascontiguousarray(np.loadtxt(path, usecols=(0, 2), unpack=True))

    @property
    def duration_seconds(self) -> float:
        return self.duration_years * YEAR_IN_SECONDS

    @property
    def sensitivity_file_name(self) -> str:
        return os.path.splitext(self.sensitivity_path)[0]


MISSION_PROFILES: list[MissionProfile] = [
    MissionProfile(
        name="Science Requirements Document (3 years)",
        duration=3,
        sensitivity_path="ScienceRequirements.txt",
        sensitivity_path_lite="ScienceRequirementsLite.txt"
    ),
    MissionProfile(
        name="Science Requirements Document (7 years)",
        duration=7,
        sensitivity_path="ScienceRequirements.txt",
        sensitivity_path_lite="ScienceRequirementsLite.txt"
    ),
    # MissionProfile(
    #     name="Cfgv1 L6A2M5N2P2D28",
    #     duration=-1,
    #     sensitivity_path="Sens_L6A2M5N2P2D28.txt",
    #     sensitivity_path_lite="Sens_L6A2M5N2P2D28_Lite.txt",
    #     notes="This corresponds to one of the sensitivity curves (C1) used in 1512.06239"
    # )
]
for i, profile in enumerate(MISSION_PROFILES):
    profile.ind = i

MISSION_PROFILE_CHOICES: list[tuple[int, str]] = [(i, profile.name) for i, profile in enumerate(MISSION_PROFILES)]
DEFAULT_MISSION_PROFILE: MissionProfile = MISSION_PROFILES[0]
