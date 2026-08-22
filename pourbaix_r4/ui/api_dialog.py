"""Masked API-key settings dialog without network activity."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import QUrl, Signal
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout

from pourbaix_r4.credentials import CredentialStore, api_docs_url, api_key_url, forget_saved_key, remember_api_key


class ApiSettingsDialog(QDialog):
    credentials_changed = Signal()

    def __init__(self, *, store: CredentialStore, open_url=None, parent=None):
        super().__init__(parent)
        self._store = store
        self._open_url = open_url or (lambda url: webbrowser.open(url.toString()))
        layout = QVBoxLayout(self)
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_input)
        remember = QPushButton("Remember on this computer"); remember.clicked.connect(self.remember_current_key); layout.addWidget(remember)
        forget = QPushButton("Forget saved key"); forget.clicked.connect(self.forget_saved_key); layout.addWidget(forget)

    def remember_current_key(self) -> None:
        remember_api_key(self._store, self.api_input.text())
        self.credentials_changed.emit()

    def forget_saved_key(self) -> None:
        forget_saved_key(self._store)
        self.credentials_changed.emit()

    def open_key_page(self) -> None:
        self._open_url(QUrl(api_key_url()))

    def open_documentation(self) -> None:
        self._open_url(QUrl(api_docs_url()))
