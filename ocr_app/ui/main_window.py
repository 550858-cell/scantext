"""Main window: capture buttons, result editor, history, tray."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core import clipboard
from ..core.config import load_settings, save_settings
from ..core.history import History
from ..core.hotkeys import HotkeyManager
from ..core.ocr_engine import OCREngine
from ..core.workers import OCRWorker, WarmupWorker
from .loading_dialog import LoadingDialog
from .settings_dialog import SettingsDialog
from .snip_overlay import SnipOverlay

IMAGE_FILTER = (
    "Изображения (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif)"
)


class MainWindow(QMainWindow):
    _hotkey_signal = pyqtSignal()

    def __init__(self, icon: QIcon) -> None:
        super().__init__()
        self._icon = icon
        self.setWindowIcon(icon)
        self.setWindowTitle("SimpleOCR — копирование текста с экрана")
        self.resize(820, 560)

        self._settings = load_settings()
        self._history = History()
        self._hotkeys = HotkeyManager()
        self._overlay: SnipOverlay | None = None
        self._worker: OCRWorker | None = None
        self._warmup: WarmupWorker | None = None
        self._loading: LoadingDialog | None = None

        self._build_ui()
        self._build_tray()
        self._refresh_history()

        self._hotkey_signal.connect(self.start_snip)
        self._register_hotkey()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Left: history panel
        left = QVBoxLayout()
        left.addWidget(QLabel("История (последние 10):"))
        self._history_list = QListWidget()
        self._history_list.setMaximumWidth(220)
        self._history_list.itemClicked.connect(self._on_history_click)
        left.addWidget(self._history_list)
        clear_btn = QPushButton("Очистить историю")
        clear_btn.clicked.connect(self._clear_history)
        left.addWidget(clear_btn)
        root.addLayout(left)

        # Right: actions + result
        right = QVBoxLayout()
        actions = QHBoxLayout()

        snip_btn = QPushButton("Захват области")
        snip_btn.clicked.connect(self.start_snip)
        actions.addWidget(snip_btn)

        open_btn = QPushButton("Открыть изображение")
        open_btn.clicked.connect(self.open_image)
        actions.addWidget(open_btn)

        clip_btn = QPushButton("Из буфера")
        clip_btn.clicked.connect(self.from_clipboard)
        actions.addWidget(clip_btn)

        settings_btn = QPushButton("Настройки")
        settings_btn.clicked.connect(self.open_settings)
        actions.addWidget(settings_btn)
        right.addLayout(actions)

        self._result = QTextEdit()
        self._result.setPlaceholderText(
            "Распознанный текст появится здесь и будет скопирован "
            "в буфер обмена автоматически."
        )
        right.addWidget(self._result)

        copy_again = QPushButton("Скопировать снова")
        copy_again.clicked.connect(self._copy_again)
        right.addWidget(copy_again)

        root.addLayout(right, stretch=1)

        self.setStatusBar(QStatusBar())
        hk = self._settings.get("hotkey", "ctrl+shift+s")
        self.statusBar().showMessage(f"Готово. Горячая клавиша: {hk}")

    def _build_tray(self) -> None:
        self._tray = QSystemTrayIcon(self._icon, self)
        self._tray.setToolTip("SimpleOCR")
        menu = QMenu()

        show_action = QAction("Открыть окно", self)
        show_action.triggered.connect(self._restore_window)
        menu.addAction(show_action)

        snip_action = QAction("Захват области", self)
        snip_action.triggered.connect(self.start_snip)
        menu.addAction(snip_action)

        menu.addSeparator()
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ---------- Capture entry points ----------

    def start_snip(self) -> None:
        if self._overlay is not None:
            return
        self.showMinimized()
        self._overlay = SnipOverlay()
        self._overlay.captured.connect(self._on_region_captured)
        self._overlay.cancelled.connect(self._on_snip_cancelled)
        self._overlay.showFullScreen()

    def _on_snip_cancelled(self) -> None:
        self._overlay = None
        self.statusBar().showMessage("Захват отменён.")

    def _on_region_captured(self, image_ndarray) -> None:
        self._overlay = None
        self._restore_window()
        self._run_ocr(image_ndarray)

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", IMAGE_FILTER
        )
        if path:
            self._run_ocr(path)

    def from_clipboard(self) -> None:
        image = clipboard.get_clipboard_image()
        if image is None:
            QMessageBox.information(
                self, "Буфер обмена", "В буфере обмена нет изображения."
            )
            return
        self._run_ocr(image)

    # ---------- OCR pipeline ----------

    def _run_ocr(self, image) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.statusBar().showMessage("Подождите, идёт распознавание…")
            return

        lang = self._settings.get("active_lang", "ru")
        use_cls = self._settings.get("use_angle_cls", True)

        if not OCREngine._instances.get((lang, use_cls)):
            self._show_loading()
            self._warmup = WarmupWorker(lang, use_cls)
            self._warmup.finished_ok.connect(
                lambda: self._after_warmup(image, lang, use_cls)
            )
            self._warmup.failed.connect(self._on_ocr_error)
            self._warmup.start()
            return

        self._start_ocr_worker(image, lang, use_cls)

    def _after_warmup(self, image, lang, use_cls) -> None:
        self._hide_loading()
        self._start_ocr_worker(image, lang, use_cls)

    def _start_ocr_worker(self, image, lang, use_cls) -> None:
        self.statusBar().showMessage("Распознавание…")
        self._worker = OCRWorker(image, lang, use_cls)
        self._worker.done.connect(self._on_ocr_done)
        self._worker.failed.connect(self._on_ocr_error)
        self._worker.start()

    def _on_ocr_done(self, text: str) -> None:
        if not text:
            self.statusBar().showMessage("Текст не распознан.")
            return
        self._result.setPlainText(text)
        if self._settings.get("auto_copy", True):
            clipboard.copy_text(text)
            self.statusBar().showMessage(
                "Готово. Текст скопирован в буфер обмена."
            )
        else:
            self.statusBar().showMessage("Готово.")
        self._history.add(text)
        self._refresh_history()

    def _on_ocr_error(self, message: str) -> None:
        self._hide_loading()
        QMessageBox.critical(
            self, "Ошибка распознавания", f"Не удалось распознать текст:\n{message}"
        )
        self.statusBar().showMessage("Ошибка распознавания.")

    def _show_loading(self) -> None:
        if self._loading is None:
            self._loading = LoadingDialog(self)
        self._loading.show()

    def _hide_loading(self) -> None:
        if self._loading is not None:
            self._loading.hide()

    # ---------- History ----------

    def _refresh_history(self) -> None:
        self._history_list.clear()
        for entry in self._history.entries():
            preview = entry["text"].replace("\n", " ")[:40]
            item = QListWidgetItem(f"{entry['time']}\n{preview}")
            item.setData(Qt.ItemDataRole.UserRole, entry["text"])
            self._history_list.addItem(item)

    def _on_history_click(self, item: QListWidgetItem) -> None:
        self._result.setPlainText(item.data(Qt.ItemDataRole.UserRole))

    def _clear_history(self) -> None:
        self._history.clear()
        self._refresh_history()

    def _copy_again(self) -> None:
        clipboard.copy_text(self._result.toPlainText())
        self.statusBar().showMessage("Скопировано в буфер обмена.")

    # ---------- Settings ----------

    def open_settings(self) -> None:
        old_langs = set(self._settings.get("languages", []))
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            new_settings = dialog.result_settings()
            if set(new_settings.get("languages", [])) != old_langs or (
                new_settings.get("active_lang")
                != self._settings.get("active_lang")
            ):
                OCREngine.clear_cache()
            self._settings = new_settings
            save_settings(self._settings)
            self._register_hotkey()
            self.statusBar().showMessage(
                f"Настройки сохранены. Горячая клавиша: "
                f"{self._settings.get('hotkey')}"
            )

    def _register_hotkey(self) -> None:
        combo = self._settings.get("hotkey", "ctrl+shift+s")
        ok = self._hotkeys.register(combo, self._hotkey_signal.emit)
        if not ok:
            self.statusBar().showMessage(
                f"Не удалось зарегистрировать горячую клавишу '{combo}'."
            )

    # ---------- Tray / window lifecycle ----------

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_window()

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if self._settings.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "SimpleOCR",
                "Приложение свёрнуто в трей. Горячая клавиша работает.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            self._quit()

    def _quit(self) -> None:
        self._hotkeys.unregister()
        self._tray.hide()
        QApplication.quit()
