"""Clipboard helpers.

Text goes through pyperclip. Reading an *image* out of the Windows
clipboard uses Pillow's ImageGrab (which itself relies on pywin32 /
the Win32 clipboard). A non-Windows fallback keeps imports safe during
testing.
"""
from __future__ import annotations

import io

import pyperclip


def copy_text(text: str) -> None:
    pyperclip.copy(text or "")


def get_clipboard_image():
    """Return a PIL.Image from the clipboard, or None.

    Handles both a raw bitmap (e.g. screenshot) and a file path copied
    in Explorer.
    """
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        return None

    try:
        data = ImageGrab.grabclipboard()
    except (OSError, NotImplementedError):
        return None

    if data is None:
        return None

    if isinstance(data, list):  # list of file paths
        for path in data:
            lower = str(path).lower()
            if lower.endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif")
            ):
                try:
                    return Image.open(path)
                except OSError:
                    continue
        return None

    if isinstance(data, Image.Image):
        return data

    if isinstance(data, (bytes, bytearray)):
        try:
            return Image.open(io.BytesIO(data))
        except OSError:
            return None

    return None
