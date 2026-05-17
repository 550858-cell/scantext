"""QThread workers so the UI never blocks on PaddleOCR."""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from .ocr_engine import OCREngine


class WarmupWorker(QThread):
    """First-run model init/download (the slow ~5-15s + download step)."""

    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, lang: str, use_angle_cls: bool) -> None:
        super().__init__()
        self._lang = lang
        self._use_angle_cls = use_angle_cls

    def run(self) -> None:
        try:
            OCREngine.warmup(self._lang, self._use_angle_cls)
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - surface any init error to UI
            self.failed.emit(str(exc))


class OCRWorker(QThread):
    """Run recognition on an image off the UI thread."""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, image, lang: str, use_angle_cls: bool) -> None:
        super().__init__()
        self._image = image
        self._lang = lang
        self._use_angle_cls = use_angle_cls

    def run(self) -> None:
        try:
            text = OCREngine.recognize(
                self._image, self._lang, self._use_angle_cls
            )
            self.done.emit(text)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
