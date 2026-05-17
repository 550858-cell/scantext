"""Modal shown during the one-time PaddleOCR model download/init."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)


class LoadingDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SimpleOCR")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setFixedSize(420, 150)

        layout = QVBoxLayout(self)

        title = QLabel("Загрузка моделей распознавания")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        msg = QLabel(
            "Это разовая операция. Модели (~10–50 МБ на язык) "
            "скачиваются один раз и сохраняются локально.\n"
            "Для первого запуска нужен интернет."
        )
        msg.setWordWrap(True)
        layout.addWidget(msg)

        bar = QProgressBar()
        bar.setRange(0, 0)  # indeterminate spinner
        layout.addWidget(bar)
