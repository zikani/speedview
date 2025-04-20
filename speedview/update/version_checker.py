import requests

class VersionChecker:
    def __init__(self, current_version):
        self.current_version = current_version
        self.update_url = "https://example.com/latest_version"  # Replace with your actual URL

    def check_for_updates(self):
        try:
            response = requests.get(self.update_url)
            latest_version = response.text.strip()  # Assuming the response is just the version number
            return latest_version > self.current_version
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False
