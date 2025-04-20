import ctypes
import sys
import win32api
import win32con
from PyQt5.QtWidgets import QMessageBox

class WindowsErrorHandler:
    @staticmethod
    def handle_win_error(error_code, parent=None):
        """Handle Windows-specific errors"""
        try:
            message = win32api.FormatMessage(error_code)
            title = f"Error (Code: {error_code})"
            
            if parent:
                QMessageBox.critical(parent, title, message)
            return message
        except:
            return f"Unknown Windows error: {error_code}"

    @staticmethod
    def check_admin():
        """Check if application has admin rights"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def request_admin():
        """Request elevation to admin privileges"""
        if not WindowsErrorHandler.check_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
        return False

    @staticmethod
    def handle_access_denied(path, parent=None):
        """Handle access denied errors"""
        message = (f"Access denied to {path}\n\n"
                  "The application may need administrative privileges.\n"
                  "Would you like to restart with elevated privileges?")
        
        if parent and QMessageBox.question(parent, "Access Denied", message) == QMessageBox.Yes:
            return WindowsErrorHandler.request_admin()
        return False