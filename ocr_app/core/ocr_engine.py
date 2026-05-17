"""Thin wrapper around PaddleOCR.

PaddleOCR (2.7.x) downloads its detection/recognition/classifier models
on first use into ``~/.paddleocr``. To keep everything self-contained
under ``%APPDATA%/SimpleOCR/models`` we redirect the user-home that
``os.path.expanduser`` resolves *before* paddleocr is imported. This is
process-scoped (we only set it for our own process) so it does not touch
the real user profile.

The import of paddleocr is deliberately lazy: it is heavy (several
seconds) and must happen off the UI thread.
"""
from __future__ import annotations

import os
from pathlib import Path

from .config import models_dir


def _redirect_paddle_home() -> None:
    """Make paddleocr place ``~/.paddleocr`` inside our models dir."""
    home = str(models_dir())
    # os.path.expanduser on Windows prefers USERPROFILE, then
    # HOMEDRIVE+HOMEPATH; on POSIX it uses HOME.
    os.environ["USERPROFILE"] = home
    os.environ["HOME"] = home
    drive, tail = os.path.splitdrive(home)
    if drive:
        os.environ["HOMEDRIVE"] = drive
        os.environ["HOMEPATH"] = tail or "\\"


class OCREngine:
    """Lazy, cached PaddleOCR instances — one per (lang, use_angle_cls)."""

    _instances: dict[tuple[str, bool], object] = {}

    @classmethod
    def get(cls, lang: str = "ru", use_angle_cls: bool = True):
        key = (lang, use_angle_cls)
        if key not in cls._instances:
            _redirect_paddle_home()
            from paddleocr import PaddleOCR  # noqa: WPS433 (lazy heavy import)

            cls._instances[key] = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                show_log=False,
            )
        return cls._instances[key]

    @classmethod
    def clear_cache(cls) -> None:
        """Drop cached instances (call when languages change)."""
        cls._instances.clear()

    @classmethod
    def warmup(cls, lang: str = "ru", use_angle_cls: bool = True) -> None:
        """Force model download / init. Safe to call from a worker thread."""
        cls.get(lang, use_angle_cls)

    @staticmethod
    def _sort_lines(result_block: list) -> str:
        """Reconstruct reading order: top→bottom, then left→right.

        Boxes whose top edge falls within ~15px are treated as the same
        visual line and ordered by their left edge.
        """
        lines = []
        for box, (text, _conf) in result_block:
            y_top = min(p[1] for p in box)
            x_left = min(p[0] for p in box)
            lines.append((y_top, x_left, text))
        lines.sort(key=lambda t: (round(t[0] / 15), t[1]))
        return "\n".join(t[2] for t in lines)

    @classmethod
    def recognize(
        cls,
        image,
        lang: str = "ru",
        use_angle_cls: bool = True,
    ) -> str:
        """Run OCR on a file path, PIL image or numpy ndarray."""
        import numpy as np

        ocr = cls.get(lang, use_angle_cls)

        if isinstance(image, Path):
            image = str(image)
        elif not isinstance(image, (str, np.ndarray)):
            # PIL.Image or similar — convert to RGB ndarray
            image = np.array(image.convert("RGB"))

        result = ocr.ocr(image, cls=use_angle_cls)
        if not result or not result[0]:
            return ""
        return cls._sort_lines(result[0])
