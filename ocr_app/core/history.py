"""Recognition history — last 10 entries, persisted as JSON."""
from __future__ import annotations

import json
from datetime import datetime

from .config import history_path

MAX_ENTRIES = 10


class History:
    def __init__(self) -> None:
        self._entries: list[dict] = []
        self.load()

    def load(self) -> None:
        path = history_path()
        if path.exists():
            try:
                self._entries = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._entries = []

    def save(self) -> None:
        history_path().write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        entry = {
            "text": text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._entries.insert(0, entry)
        del self._entries[MAX_ENTRIES:]
        self.save()

    def entries(self) -> list[dict]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        self.save()
