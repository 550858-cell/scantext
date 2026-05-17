"""Settings: languages, angle classifier, hotkey, auto-copy."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

from ..core.config import SUPPORTED_LANGS


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(380)
        self._settings = dict(settings)

        root = QVBoxLayout(self)
        form = QFormLayout()

        root.addWidget(QLabel("Доступные языки (отметьте нужные):"))
        self._lang_list = QListWidget()
        for code, name in SUPPORTED_LANGS:
            item = QListWidgetItem(f"{name}  [{code}]")
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = code in self._settings.get("languages", [])
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
            self._lang_list.addItem(item)
        root.addWidget(self._lang_list)

        self._active_lang = QComboBox()
        self._refresh_active_lang()
        self._lang_list.itemChanged.connect(self._refresh_active_lang)
        form.addRow("Активный язык:", self._active_lang)

        self._angle_cls = QCheckBox("Угловой классификатор (повёрнутый текст)")
        self._angle_cls.setChecked(self._settings.get("use_angle_cls", True))
        form.addRow(self._angle_cls)

        self._hotkey = QLineEdit(self._settings.get("hotkey", "ctrl+shift+s"))
        form.addRow("Горячая клавиша:", self._hotkey)

        self._auto_copy = QCheckBox("Автокопирование результата в буфер")
        self._auto_copy.setChecked(self._settings.get("auto_copy", True))
        form.addRow(self._auto_copy)

        self._tray = QCheckBox("Сворачивать в системный трей")
        self._tray.setChecked(self._settings.get("minimize_to_tray", True))
        form.addRow(self._tray)

        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _checked_langs(self) -> list[str]:
        langs = []
        for i in range(self._lang_list.count()):
            item = self._lang_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                langs.append(item.data(Qt.ItemDataRole.UserRole))
        return langs

    def _refresh_active_lang(self) -> None:
        current = self._active_lang.currentData()
        self._active_lang.clear()
        for code in self._checked_langs() or ["ru"]:
            self._active_lang.addItem(code, code)
        if current is not None:
            idx = self._active_lang.findData(current)
            if idx >= 0:
                self._active_lang.setCurrentIndex(idx)

    def result_settings(self) -> dict:
        langs = self._checked_langs() or ["ru"]
        active = self._active_lang.currentData() or langs[0]
        self._settings.update(
            {
                "languages": langs,
                "active_lang": active,
                "use_angle_cls": self._angle_cls.isChecked(),
                "hotkey": self._hotkey.text().strip() or "ctrl+shift+s",
                "auto_copy": self._auto_copy.isChecked(),
                "minimize_to_tray": self._tray.isChecked(),
            }
        )
        return self._settings
