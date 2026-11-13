"""Optional C++17 FIFO primitive with an equivalent Python reference."""
from __future__ import annotations

import ctypes
from pathlib import Path


def consume(eligible: int, ahead: int, remaining: int) -> tuple[int, int]:
    if eligible <= 0 or remaining <= 0:
        return 0, ahead
    cleared = min(ahead, eligible)
    return min(remaining, eligible - cleared), ahead - cleared


class NativeExecution:
    def __init__(self, path: str | Path):
        self.library = ctypes.CDLL(str(Path(path).resolve()))
        self.function = self.library.consume
        self.function.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), ctypes.c_int64]
        self.function.restype = ctypes.c_int64

    def __call__(self, eligible: int, ahead: int, remaining: int) -> tuple[int, int]:
        queue = ctypes.c_int64(ahead)
        fill = self.function(eligible, ctypes.byref(queue), remaining)
        return fill, queue.value
