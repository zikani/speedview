import os
import sys
import json
import requests
import tempfile
import subprocess
from packaging import version
from PyQt5.QtWidgets import QMessageBox

from speedview.update.version_checker import VersionChecker
from ..config.config import APP_VERSION, APP_NAME

class UpdateChecker:
    def __init__(self, settings=None):
        self.current_version = APP_VERSION
        if settings and hasattr(settings, 'update_url'):
            self.github_api_url = settings.update_url
        else:
            from speedview.config.config import DEFAULT_UPDATE_URL
            self.github_api_url = DEFAULT_UPDATE_URL
        self.update_available = False
        self.latest_version = None
        self.release_notes = None
        self.download_url = None

    def check_for_updates(self):
        try:
            response = requests.get(self.github_api_url, timeout=5)
            try:
                response.raise_for_status()  # Raise exception for bad status codes
            except requests.exceptions.HTTPError as http_err:
                print(f"Update check HTTP error: {http_err}")
                return False
            
            data = response.json()
            self.latest_version = data['tag_name'].replace('v', '')
            self.release_notes = data.get('body', 'No release notes available')
            
            if version.parse(self.latest_version) > version.parse(self.current_version):
                self.update_available = True
                for asset in data['assets']:
                    if asset['name'].endswith('.exe'):
                        self.download_url = asset['browser_download_url']
                        break
            return self.update_available
        except Exception as e:
            print(f"Update check failed: {e}")
            return False

    def download_update(self, progress_callback=None):
        if not self.download_url:
            return None

        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
            
            downloaded = 0
            with temp_file as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        if progress_callback and total_size:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            return temp_file.name
        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def install_update(self, update_file):
        try:
            if not os.path.exists(update_file):
                raise FileNotFoundError("Update file not found")

            # Create and execute update script
            script_path = self._create_update_script(update_file)
            subprocess.Popen(['cmd', '/c', script_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def _create_update_script(self, update_file):
        script_content = f'''@echo off
timeout /t 2 /nobreak > nul
start "" /wait "{update_file}"
del "{update_file}"
del "%~f0"
'''
        script_path = os.path.join(tempfile.gettempdir(), 'update_network_speed_meter.bat')
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def check_updates(self):
        """Check for software updates"""
        try:
            version_checker = VersionChecker(APP_VERSION)  # Use the current app version
            has_update = version_checker.check_for_updates()
            
            if has_update:
                reply = QMessageBox.question(self, "Update Available",
                    "A new version is available. Would you like to update now?",
                    QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.start_update()  # Call the start_update method
            else:
                QMessageBox.information(self, "Up to Date",
                    "You are running the latest version.")
        except Exception as e:
            QMessageBox.warning(self, "Update Check Failed",
                f"Could not check for updates:\n{str(e)}")