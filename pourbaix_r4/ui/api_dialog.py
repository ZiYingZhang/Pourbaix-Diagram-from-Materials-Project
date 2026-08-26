"""Masked API-key settings dialog without network activity."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import QUrl, Signal
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from pourbaix_r4.credentials import CredentialError, CredentialStore, api_docs_url, api_key_url, forget_saved_key, remember_api_key


class ApiSettingsDialog(QDialog):
    credentials_changed = Signal()

    def __init__(self, *, store: CredentialStore, open_url=None, parent=None):
        super().__init__(parent)
        self._store = store
        self._open_url = open_url or (lambda url: webbrowser.open(url.toString()))
        self.session_api_key: str | None = None
        layout = QVBoxLayout(self)
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_input)
        self.api_key_link = QPushButton("Get a Materials Project API key")
        self.api_key_link.setFlat(True)
        self.api_key_link.setStyleSheet("QPushButton { color: #2f80ed; text-decoration: underline; text-align: left; }")
        self.api_key_link.clicked.connect(self.open_key_page)
        layout.addWidget(self.api_key_link)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        use_session = QPushButton("Use for this session"); use_session.clicked.connect(self.use_current_key_for_session); layout.addWidget(use_session)
        remember = QPushButton("Remember and use"); remember.clicked.connect(self.remember_current_key); layout.addWidget(remember)
        forget = QPushButton("Forget saved key"); forget.clicked.connect(self.forget_saved_key); layout.addWidget(forget)

    def use_current_key_for_session(self) -> None:
        value = self.api_input.text().strip()
        if not value:
            self.status.setText("Enter a Materials Project API key first.")
            return
        self.session_api_key = value
        self.credentials_changed.emit()
        self.accept()

    def remember_current_key(self) -> None:
        try:
            remember_api_key(self._store, self.api_input.text())
        except CredentialError as error:
            self.status.setText(str(error))
            return
        self.session_api_key = self.api_input.text().strip()
        self.credentials_changed.emit()
        self.accept()

    def forget_saved_key(self) -> None:
        try:
            forget_saved_key(self._store)
        except CredentialError as error:
            self.status.setText(str(error))
            return
        self.session_api_key = None
        self.api_input.clear()
        self.credentials_changed.emit()
        self.accept()

    def open_key_page(self) -> None:
        self._open_url(QUrl(api_key_url()))

    def open_documentation(self) -> None:
        self._open_url(QUrl(api_docs_url()))
