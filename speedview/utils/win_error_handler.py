import ctypes
import os
import platform
import sys
from PyQt5.QtWidgets import QMessageBox

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import win32api
    import win32con
else:
    win32api = None
    win32con = None


class WindowsErrorHandler:
    @staticmethod
    def handle_win_error(error_code, parent=None):
        """Handle Windows-specific errors"""
        if not IS_WINDOWS or win32api is None:
            return f"System error code: {error_code}"
        try:
            message = win32api.FormatMessage(error_code)
            title = f"Error (Code: {error_code})"

            if parent:
                QMessageBox.critical(parent, title, message)
            return message
        except Exception:
            return f"Unknown Windows error: {error_code}"

    @staticmethod
    def check_admin():
        """Check if application has admin/root rights"""
        if not IS_WINDOWS:
            try:
                return os.geteuid() == 0
            except Exception:
                return False
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def request_admin():
        """Request elevation to admin privileges"""
        if not IS_WINDOWS:
            return False
        if not WindowsErrorHandler.check_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
        return False

    @staticmethod
    def handle_access_denied(path, parent=None):
        """Handle access denied errors"""
        message = (
            f"Access denied to {path}\n\n"
            "The application may need elevated privileges."
        )
        if IS_WINDOWS:
            message += "\nWould you like to restart with elevated privileges?"
            if parent and QMessageBox.question(parent, "Access Denied", message) == QMessageBox.Yes:
                return WindowsErrorHandler.request_admin()
        elif parent:
            QMessageBox.warning(parent, "Access Denied", message)
        return False