import numpy as np


def make_minor_ticks(min: int, max: int) -> np.ndarray:
    ticks = np.array([])
    for i in range(min, max):
        ticks = np.append(ticks, np.linspace(10 ** i, 10 ** (i + 1), 9, endpoint=False))
    return np.log10(ticks)
