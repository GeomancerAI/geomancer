"""PySide6 desktop shell for Geomancer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from desktop.bridge import GeomancerBridge


DESKTOP_DIR = Path(__file__).resolve().parent
UI_ENTRYPOINT = DESKTOP_DIR / "ui" / "index.html"
WINDOW_ICON_PATH = DESKTOP_DIR / "ui" / "assets" / "logo" / "geomancer-icon.png"


class GeomancerDesktopWindow(QMainWindow):
    """Primary desktop window that hosts the embedded HTML/CSS/JS UI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Geomancer Alpha")
        self.resize(1480, 940)
        self.setMinimumSize(1180, 760)
        if WINDOW_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(WINDOW_ICON_PATH)))

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        self.bridge = GeomancerBridge()
        self.channel = QWebChannel(self.web_view.page())
        self.channel.registerObject("geomancerBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        self._build_menu()
        self._load_ui()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        reload_action = QAction("Reload UI", self)
        reload_action.triggered.connect(self._reload_ui_clean_dev)
        file_menu.addAction(reload_action)

        open_blender_action = QAction("Open Latest In Blender", self)
        open_blender_action.triggered.connect(self._open_latest_in_blender)
        file_menu.addAction(open_blender_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _load_ui(self) -> None:
        if not UI_ENTRYPOINT.exists():
            raise FileNotFoundError(f"Desktop UI entrypoint not found: {UI_ENTRYPOINT}")
        self.web_view.load(QUrl.fromLocalFile(str(UI_ENTRYPOINT)))

    def _reload_ui_clean_dev(self) -> None:
        try:
            cleanup_payload = json.loads(self.bridge.cleanDevReload())
            for message in cleanup_payload.get("messages", []):
                self.bridge.logMessage.emit(f"[reload] {message}")
            self.bridge.logMessage.emit("[reload] Desktop UI reload requested.")
        except Exception as error:
            self.bridge.logMessage.emit(f"[reload] Cleanup step failed: {error}")
        finally:
            try:
                self.web_view.page().triggerAction(QWebEnginePage.WebAction.ReloadAndBypassCache)
            except Exception:
                self.web_view.reload()

    def _open_latest_in_blender(self) -> None:
        result_json = self.bridge.openLatestInBlender()
        QMessageBox.information(self, "Geomancer", result_json)


def run() -> int:
    """Run the desktop shell."""
    app = QApplication(sys.argv)
    app.setApplicationName("Geomancer")
    app.setOrganizationName("Geomancer")
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    if WINDOW_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(WINDOW_ICON_PATH)))

    window = GeomancerDesktopWindow()
    window.show()
    return app.exec()
