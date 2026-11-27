import os
import platform
import subprocess
import tempfile
import webbrowser
import requests
from packaging import version

from ..config.config import APP_VERSION, DEFAULT_RELEASES_PAGE_URL, DEFAULT_UPDATE_URL


class UpdateChecker:
    def __init__(self, settings=None):
        self.current_version = APP_VERSION
        if settings and getattr(settings, 'update_url', None):
            self.github_api_url = settings.update_url
        else:
            self.github_api_url = DEFAULT_UPDATE_URL
        self.update_available = False
        self.latest_version = None
        self.release_notes = None
        self.download_url = None
        self.release_page_url = DEFAULT_RELEASES_PAGE_URL

    def check_for_updates(self):
        try:
            response = requests.get(self.github_api_url, timeout=5)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                print(f"Update check HTTP error: {http_err}")
                return False

            data = response.json()
            self.latest_version = data.get('tag_name', '').lstrip('v').strip()
            self.release_notes = data.get('body', 'No release notes available')
            self.release_page_url = data.get('html_url') or DEFAULT_RELEASES_PAGE_URL
            self.download_url = None

            if self.latest_version and version.parse(self.latest_version) > version.parse(self.current_version):
                self.update_available = True
                for asset in data.get('assets', []):
                    name = asset.get('name', '').lower()
                    if platform.system() == "Windows" and name.endswith('.exe'):
                        self.download_url = asset.get('browser_download_url')
                        break
                    if platform.system() != "Windows" and name.endswith(('.tar.gz', '.appimage', '.deb')):
                        self.download_url = asset.get('browser_download_url')
                        break
                if not self.download_url:
                    self.download_url = self.release_page_url
            return self.update_available
        except Exception as e:
            print(f"Update check failed: {e}")
            return False

    def open_release_page(self):
        """Open the GitHub release page in the system web browser."""
        target = self.release_page_url or self.download_url or DEFAULT_RELEASES_PAGE_URL
        return webbrowser.open(target)

    def download_update(self, progress_callback=None):
        if platform.system() != "Windows":
            # On Linux/macOS, open release page in browser rather than downloading a Windows .exe
            self.open_release_page()
            return self.release_page_url

        if not self.download_url or self.download_url == self.release_page_url:
            self.open_release_page()
            return None

        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
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
        if platform.system() != "Windows":
            return self.open_release_page()

        try:
            if not update_file or not os.path.exists(update_file):
                raise FileNotFoundError("Update file not found")

            script_path = self._create_update_script(update_file)
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(['cmd', '/c', script_path], creationflags=creationflags)
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