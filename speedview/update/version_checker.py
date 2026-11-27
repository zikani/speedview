import requests
from packaging import version
from speedview.config.config import DEFAULT_UPDATE_URL


class VersionChecker:
    def __init__(self, current_version, update_url=None):
        self.current_version = current_version
        self.update_url = update_url or DEFAULT_UPDATE_URL
        self.latest_version = None
        self.release_url = None
        self.release_notes = None

    def check_for_updates(self):
        try:
            response = requests.get(self.update_url, timeout=5)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "json" in content_type or response.text.lstrip().startswith("{"):
                data = response.json()
                tag = data.get("tag_name", "").lstrip("v").strip()
                self.latest_version = tag or None
                self.release_url = data.get("html_url")
                self.release_notes = data.get("body", "")
            else:
                self.latest_version = response.text.strip().lstrip("v")
            if not self.latest_version:
                return False
            return version.parse(self.latest_version) > version.parse(self.current_version)
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False
