"""SimpleOCR — entry point.

Run: python -m ocr_app.main   (from the project root)
or:  python ocr_app/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication


def _app_icon() -> QIcon:
    """Use bundled icon.ico if present, else draw a simple fallback."""
    ico = Path(__file__).parent / "resources" / "icon.ico"
    if ico.exists():
        return QIcon(str(ico))

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(0, 122, 204))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setPen(QColor("white"))
    font = QFont("Arial", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(
        pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "OCR"
    )
    painter.end()
    return QIcon(pixmap)


def main() -> int:
    # Allow running as a script (no package context).
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).parent.parent))

    from ocr_app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("SimpleOCR")
    # Keep running in the tray after the window is closed.
    app.setQuitOnLastWindowClosed(False)

    icon = _app_icon()
    app.setWindowIcon(icon)

    window = MainWindow(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
