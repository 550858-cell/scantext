"""Fullscreen 'snipping' overlay: dim the screen, drag a rectangle."""
from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QKeyEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class SnipOverlay(QWidget):
    """Emits ``captured`` with an RGB numpy ndarray, or ``cancelled``."""

    captured = pyqtSignal(object)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Span the full virtual desktop (all monitors).
        geo = QRect()
        for screen in QGuiApplication.screens():
            geo = geo.united(screen.geometry())
        self._virtual_geo = geo
        self.setGeometry(geo)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None

    def _selection_rect(self) -> QRect:
        if self._origin is None or self._current is None:
            return QRect()
        return QRect(self._origin, self._current).normalized()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        rect = self._selection_rect()
        if not rect.isNull():
            # Clear the dim inside the selection.
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(0, 174, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._origin is not None:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rect = self._selection_rect()
        self.hide()
        if rect.width() < 5 or rect.height() < 5:
            self.cancelled.emit()
            return
        self._grab(rect)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def _grab(self, rect: QRect) -> None:
        # Map widget-local rect to absolute virtual-desktop coordinates.
        abs_left = self._virtual_geo.left() + rect.left()
        abs_top = self._virtual_geo.top() + rect.top()

        import mss

        region = {
            "left": int(abs_left),
            "top": int(abs_top),
            "width": int(rect.width()),
            "height": int(rect.height()),
        }
        with mss.mss() as sct:
            shot = sct.grab(region)
        # BGRA -> RGB
        arr = np.frombuffer(shot.bgra, dtype=np.uint8).reshape(
            shot.height, shot.width, 4
        )
        rgb = arr[:, :, [2, 1, 0]].copy()
        self.captured.emit(rgb)
