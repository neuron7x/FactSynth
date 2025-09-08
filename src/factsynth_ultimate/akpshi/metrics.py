
from typing import Sequence

import numpy as np


def rmse(y: Sequence[float], yhat: Sequence[float]) -> float:
    y_arr = np.asarray(y, dtype=float)
    yhat_arr = np.asarray(yhat, dtype=float)
    if y_arr.shape != yhat_arr.shape:
        raise ValueError("y and yhat must have the same shape")
    return float(np.sqrt(np.mean((y_arr - yhat_arr) ** 2)))

def fcr(num_confirmed: int, total: int) -> float:
    total = max(int(total), 1)
    num_confirmed = max(int(num_confirmed), 0)
    return float(num_confirmed / total)


def pfi(level_scores: Sequence[float]) -> float:
    arr = np.asarray(level_scores, float)
    if arr.size == 0:
        return 0.0
    arr = np.clip(arr, 0.0, 1.0)
    return float(np.mean(arr))
