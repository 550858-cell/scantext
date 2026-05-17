"""Application paths and persistent settings.

All user data lives in %APPDATA%/SimpleOCR/ on Windows. On other
platforms a sensible fallback under the user home is used so the code
remains importable/testable everywhere.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "SimpleOCR"

DEFAULT_SETTINGS = {
    "languages": ["ru", "en"],          # langs offered in the language picker
    "active_lang": "ru",                # lang passed to PaddleOCR
    "use_angle_cls": True,
    "hotkey": "ctrl+shift+s",
    "auto_copy": True,
    "minimize_to_tray": True,
}

SUPPORTED_LANGS = [
    ("ru", "Русский"),
    ("en", "English"),
    ("ch", "中文 (Chinese)"),
    ("japan", "日本語 (Japanese)"),
    ("korean", "한국어 (Korean)"),
    ("german", "Deutsch"),
    ("french", "Français"),
]


def appdata_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        root = Path(base) / APP_NAME
    else:
        root = Path.home() / f".{APP_NAME.lower()}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def models_dir() -> Path:
    d = appdata_dir() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def settings_path() -> Path:
    return appdata_dir() / "settings.json"


def history_path() -> Path:
    return appdata_dir() / "history.json"


def load_settings() -> dict:
    path = settings_path()
    data = dict(DEFAULT_SETTINGS)
    if path.exists():
        try:
            data.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_settings(settings: dict) -> None:
    settings_path().write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
