"""Global hotkey registration via the ``keyboard`` library.

The callback fires on ``keyboard``'s own background thread, so the
callback supplied by the UI must be thread-safe (in practice it just
emits a Qt signal).
"""
from __future__ import annotations

from typing import Callable

import keyboard


class HotkeyManager:
    def __init__(self) -> None:
        self._handle = None
        self._combo: str | None = None

    def register(self, combo: str, callback: Callable[[], None]) -> bool:
        self.unregister()
        try:
            self._handle = keyboard.add_hotkey(combo, callback)
            self._combo = combo
            return True
        except (ValueError, ImportError, OSError):
            self._handle = None
            self._combo = None
            return False

    def unregister(self) -> None:
        if self._handle is not None:
            try:
                keyboard.remove_hotkey(self._handle)
            except (KeyError, ValueError):
                pass
            self._handle = None
            self._combo = None
