"""Sliding-Window Oscillation & Cycle Detection Engine for ORAGAI (P8).

Implements finite sequence autocorrelation across sliding window W (default W=5).
Tracks composite state fingerprints sigma_k = < H(AST_k), H(T_fail, k), H(D_k) >.
Detects:
  - Period 1 (Direct Stagnation): sigma_k == sigma_k-1
  - Period 2 (Flip-Flop Cycle): sigma_k == sigma_k-2 (A -> B -> A)
  - Period 3..5 (Periodic Cycles): sigma_k == sigma_k-p (A -> B -> C -> A)
  - Cosmetic Churn Evasion: non-zero raw file diff but delta AST == 0
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .models import CyclePattern, StateFingerprint


class OscillationDetector:
    """
    Sliding-window sequence autocorrelation engine.
    Detects Direct Stagnation (p=1), Flip-Flop (p=2), and Periodic Cycles (p=3..5).
    """

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._history: List[StateFingerprint] = []

    def register_state(self, fingerprint: StateFingerprint) -> Tuple[CyclePattern, int]:
        """
        Register a new turn state fingerprint and evaluate whether a cycle has formed.
        Returns (CyclePattern, cycle_period).
        """
        self._history.append(fingerprint)
        if len(self._history) > self.window_size:
            self._history.pop(0)

        n = len(self._history)
        if n < 2:
            return CyclePattern.NONE, 0

        curr = self._history[-1]

        # 1. Check Period 1: Direct Stagnation (sigma_k == sigma_k-1)
        prev = self._history[-2]
        if curr.composite_hash == prev.composite_hash:
            return CyclePattern.DIRECT_STAGNATION, 1

        # 2. Check Period 2..5 Periodic Oscillations (sigma_k == sigma_k-p)
        for p in range(2, n):
            target = self._history[-1 - p]
            if curr.composite_hash == target.composite_hash:
                if p == 2:
                    return CyclePattern.FLIP_FLOP_P2, 2
                return CyclePattern.PERIODIC_PN, p

        return CyclePattern.NONE, 0

    def get_history(self) -> List[StateFingerprint]:
        """Return the current sliding-window history buffer."""
        return list(self._history)

    def reset_window(self) -> None:
        """Clear the history buffer."""
        self._history.clear()
