import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import webbrowser
import zipfile
import requests
from packaging import version

from ..config.config import (
    APP_VERSION,
    DEFAULT_RELEASES_PAGE_URL,
    DEFAULT_UPDATE_URL,
    UPDATE_CHECK_INTERVAL_SECONDS,
)


class UpdateChecker:
    """
    Cross-platform GitHub Release auto-updater (Windows, macOS, Linux).

    Enforces a 3-day check cooldown via settings.last_update_check to avoid
    GitHub API rate limits, downloads .zip release assets into a temp folder,
    extracts safely, and launches a detached helper script so the running app
    can exit, replace its files/executable cleanly, and restart.
    """

    def __init__(self, settings=None, check_interval=UPDATE_CHECK_INTERVAL_SECONDS):
        self.settings = settings
        self.check_interval = int(check_interval)
        self.current_version = APP_VERSION
        if settings and getattr(settings, 'update_url', None):
            self.github_api_url = settings.update_url
        else:
            self.github_api_url = DEFAULT_UPDATE_URL
        self.update_available = False
        self.latest_version = None
        self.release_notes = None
        self.download_url = None
        self.asset_name = None
        self.release_page_url = DEFAULT_RELEASES_PAGE_URL
        self.staged_dir = None
        self.extracted_dir = None
        self.last_helper_script = None
        self.last_helper_process = None

    def should_check_for_updates(self, force=False):
        """Return True when forced or when >= 3 days elapsed since last check."""
        if force:
            return True
        if self.settings is None:
            return True
        last_check = float(getattr(self.settings, 'last_update_check', 0.0) or 0.0)
        if last_check <= 0:
            return True
        return (time.time() - last_check) >= self.check_interval

    def _record_check_timestamp(self):
        """Persist the latest GitHub API check timestamp cleanly."""
        if self.settings is None:
            return
        try:
            self.settings.last_update_check = time.time()
            if hasattr(self.settings, 'save'):
                self.settings.save()
        except Exception as e:
            print(f"Could not persist last_update_check timestamp: {e}")

    def _select_asset_for_platform(self, assets, system_name=None):
        """Pick best release asset (preferring OS-matching .zip archive) from GitHub assets list."""
        system = (system_name or platform.system()).lower()
        normalized = []
        for asset in assets or []:
            name = str(asset.get('name', ''))
            url = asset.get('browser_download_url')
            if url:
                normalized.append((name.lower(), name, url))

        if not normalized:
            return None, None

        if system == "windows":
            priorities = [
                lambda n: n.endswith('.zip') and ('win' in n or 'windows' in n),
                lambda n: n.endswith('.zip') and not any(k in n for k in ('linux', 'mac', 'darwin', 'osx')),
                lambda n: n.endswith('.exe'),
            ]
        elif system == "darwin":
            priorities = [
                lambda n: n.endswith('.zip') and any(k in n for k in ('mac', 'darwin', 'osx')),
                lambda n: n.endswith(('.tar.gz', '.dmg')) and any(k in n for k in ('mac', 'darwin', 'osx')),
                lambda n: n.endswith('.zip') and not any(k in n for k in ('win', 'linux')),
            ]
        else:
            priorities = [
                lambda n: n.endswith('.zip') and 'linux' in n,
                lambda n: n.endswith(('.tar.gz', '.appimage', '.deb')) and 'linux' in n,
                lambda n: n.endswith('.zip') and not any(k in n for k in ('win', 'mac', 'darwin', 'osx')),
                lambda n: 'linux' in n and not n.endswith('.sha256'),
            ]

        for pred in priorities:
            for low_name, orig_name, url in normalized:
                if pred(low_name):
                    return url, orig_name
        return None, None

    def check_for_updates(self, force=False):
        """Query GitHub Releases API (at most once every 3 days unless forced)."""
        if not self.should_check_for_updates(force=force):
            return False

        self.update_available = False
        self.download_url = None
        self.asset_name = None

        try:
            headers = {
                "User-Agent": f"SpeedView/{self.current_version}",
                "Accept": "application/vnd.github+json",
            }
            response = requests.get(self.github_api_url, headers=headers, timeout=10)
            self._record_check_timestamp()

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                print(f"Update check HTTP error: {http_err}")
                return False

            data = response.json()
            self.latest_version = str(data.get('tag_name', '')).lstrip('v').strip()
            self.release_notes = data.get('body') or 'No release notes available'
            self.release_page_url = data.get('html_url') or DEFAULT_RELEASES_PAGE_URL

            if self.latest_version and version.parse(self.latest_version) > version.parse(self.current_version):
                self.update_available = True
                asset_url, asset_name = self._select_asset_for_platform(data.get('assets', []))
                if asset_url:
                    self.download_url = asset_url
                    self.asset_name = asset_name
                else:
                    self.download_url = self.release_page_url
            return self.update_available
        except Exception as e:
            print(f"Update check failed: {e}")
            return False

    def open_release_page(self):
        """Open the GitHub release page in the system web browser."""
        target = self.release_page_url or self.download_url or DEFAULT_RELEASES_PAGE_URL
        return webbrowser.open(target)

    @staticmethod
    def _safe_extract_zip(zip_path, extract_dir):
        """Extract .zip safely preventing path traversal while preserving executable bits."""
        os.makedirs(extract_dir, exist_ok=True)
        real_root = os.path.realpath(extract_dir)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                dest = os.path.realpath(os.path.join(real_root, member.filename))
                if not (dest == real_root or dest.startswith(real_root + os.sep)):
                    raise ValueError(f"Unsafe zip entry path: {member.filename}")
                if member.is_dir():
                    os.makedirs(dest, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(member, 'r') as src, open(dest, 'wb') as out:
                        shutil.copyfileobj(src, out)
                    perm = (member.external_attr >> 16) & 0o777
                    if perm:
                        try:
                            os.chmod(dest, perm)
                        except OSError:
                            pass
        return extract_dir

    def download_update(self, progress_callback=None):
        """Download the GitHub Release asset (.zip or binary) to a temporary staging directory."""
        if not self.download_url or self.download_url == self.release_page_url:
            return None

        try:
            self.staged_dir = tempfile.mkdtemp(prefix="speedview_update_")
            filename = self.asset_name or os.path.basename(self.download_url.split('?')[0]) or "speedview_update.zip"
            dest_path = os.path.join(self.staged_dir, filename)

            headers = {"User-Agent": f"SpeedView/{self.current_version}"}
            with requests.get(self.download_url, stream=True, headers=headers, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0) or 0)
                downloaded = 0
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=16384):
                        if not chunk:
                            continue
                        downloaded += len(chunk)
                        f.write(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(min(100.0, (downloaded / total_size) * 100.0))

            if progress_callback:
                progress_callback(100.0)

            self.extracted_dir = None
            if dest_path.lower().endswith('.zip'):
                extract_dir = os.path.join(self.staged_dir, "extracted")
                self._safe_extract_zip(dest_path, extract_dir)
                self.extracted_dir = extract_dir

            return dest_path
        except Exception as e:
            print(f"Download failed: {e}")
            return None

    @staticmethod
    def _resolve_payload(update_path):
        """Return (payload_dir, staged_root, is_extracted) from a downloaded zip, dir, or binary."""
        if os.path.isdir(update_path):
            return update_path, update_path, True
        if update_path.lower().endswith('.zip'):
            staged_root = os.path.dirname(update_path)
            extract_dir = os.path.join(staged_root, "extracted")
            if not os.path.isdir(extract_dir) or not os.listdir(extract_dir):
                UpdateChecker._safe_extract_zip(update_path, extract_dir)
            return extract_dir, staged_root, True
        return update_path, os.path.dirname(update_path), False

    @staticmethod
    def _find_app_bundle_or_binary(path):
        """For macOS .app bundles, find the *.app bundle root; otherwise return the file/dir."""
        norm = os.path.abspath(path)
        parts = norm.split(os.sep)
        for i, part in enumerate(parts):
            if part.endswith('.app'):
                return os.sep.join(parts[: i + 1]) or os.sep
        return norm

    def can_self_replace(self, target_path=None):
        """Return True if we have a safe frozen/explicit target to swap cleanly."""
        if target_path:
            return True
        return bool(getattr(sys, 'frozen', False))

    def install_update(self, update_file, target_path=None, restart=True, launch_script=True, wait_pid=None):
        """
        Launch a detached helper script that waits for the running process to exit,
        replaces the old executable/bundle files from the temp staging directory,
        removes temporary update files, and restarts the updated app.
        """
        try:
            if not update_file or not os.path.exists(update_file):
                raise FileNotFoundError(f"Update artifact not found: {update_file}")

            if not self.can_self_replace(target_path):
                # Do not destructively overwrite a live Python interpreter when running from source
                return False

            payload_path, staged_root, _ = self._resolve_payload(update_file)
            resolved_target = target_path or sys.executable
            pid_to_wait = os.getpid() if wait_pid is None else int(wait_pid)
            system = platform.system()

            if system == "Windows":
                script_path = self._create_windows_updater_script(
                    payload_path=payload_path,
                    staged_root=staged_root,
                    target_path=resolved_target,
                    pid=pid_to_wait,
                    restart=restart,
                )
                self.last_helper_script = script_path
                if launch_script:
                    flags = (
                        getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        | getattr(subprocess, "DETACHED_PROCESS", 0)
                        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    )
                    self.last_helper_process = subprocess.Popen(
                        ['cmd', '/c', script_path],
                        creationflags=flags,
                        close_fds=True,
                    )
                return True

            script_path = self._create_posix_updater_script(
                payload_path=payload_path,
                staged_root=staged_root,
                target_path=resolved_target,
                pid=pid_to_wait,
                restart=restart,
            )
            self.last_helper_script = script_path
            if launch_script:
                self.last_helper_process = subprocess.Popen(
                    ['/bin/sh', script_path],
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
            return True
        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    @staticmethod
    def _pick_source_entry(payload_path, target_basename):
        """Pick the matching file or .app inside an extracted payload folder."""
        if os.path.isfile(payload_path):
            return payload_path
        entries = os.listdir(payload_path)
        for name in entries:
            if name == target_basename:
                return os.path.join(payload_path, name)
        for name in entries:
            if name.endswith(('.exe', '.app')):
                return os.path.join(payload_path, name)
        if len(entries) == 1:
            return os.path.join(payload_path, entries[0])
        return payload_path

    def _create_windows_updater_script(self, payload_path, staged_root, target_path, pid, restart=True):
        target_abs = os.path.abspath(target_path)
        target_dir = target_abs if os.path.isdir(target_abs) else os.path.dirname(target_abs)
        target_name = os.path.basename(target_abs)
        src_entry = self._pick_source_entry(payload_path, target_name)

        if os.path.isdir(src_entry):
            replace_block = f'xcopy "{src_entry}\\*" "{target_dir}\\" /E /Y /I /Q > nul'
            restart_exe = os.path.join(target_dir, target_name) if not os.path.isdir(target_abs) else src_entry
        else:
            dest_file = target_abs if not os.path.isdir(target_abs) else os.path.join(target_dir, os.path.basename(src_entry))
            replace_block = f'copy /Y "{src_entry}" "{dest_file}" > nul'
            restart_exe = dest_file

        restart_block = f'start "" "{restart_exe}"' if restart else ''
        cleanup_staged = f'if exist "{staged_root}" rmdir /S /Q "{staged_root}"'

        wait_block = ""
        if int(pid) > 0:
            wait_block = (
                "set RETRIES=0\r\n"
                ":waitloop\r\n"
                f'tasklist /FI "PID eq {int(pid)}" 2>nul | find "{int(pid)}" >nul\r\n'
                "if %ERRORLEVEL%==0 (\r\n"
                "  set /A RETRIES+=1\r\n"
                "  if %RETRIES% LSS 20 (\r\n"
                "    timeout /t 1 /nobreak > nul\r\n"
                "    goto waitloop\r\n"
                "  )\r\n"
                ")\r\n"
            )

        script_content = (
            "@echo off\r\n"
            f"{wait_block}"
            f"{replace_block}\r\n"
            f"{cleanup_staged}\r\n"
            f"{restart_block}\r\n"
            '(goto) 2>nul & del "%~f0"\r\n'
        )
        fd, script_path = tempfile.mkstemp(prefix="speedview_updater_", suffix=".bat")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path

    def _create_posix_updater_script(self, payload_path, staged_root, target_path, pid, restart=True):
        target_bundle = self._find_app_bundle_or_binary(target_path)
        target_name = os.path.basename(target_bundle)
        src_entry = self._pick_source_entry(payload_path, target_name)

        def q(p):
            return "'" + str(p).replace("'", "'\"'\"'") + "'"

        if target_bundle.endswith('.app') and src_entry.endswith('.app'):
            replace_cmd = (
                f"rm -rf {q(target_bundle)} && "
                f"cp -Rf {q(src_entry)} {q(target_bundle)}"
            )
            relaunch_cmd = f"open -n {q(target_bundle)}" if restart else ""
        elif os.path.isdir(src_entry):
            target_dir = target_bundle if os.path.isdir(target_bundle) else os.path.dirname(target_bundle)
            replace_cmd = f"mkdir -p {q(target_dir)} && cp -Rf {q(src_entry)}/. {q(target_dir)}/"
            relaunch_target = target_bundle if os.path.isfile(target_bundle) else os.path.join(target_dir, target_name)
            relaunch_cmd = f"nohup {q(relaunch_target)} >/dev/null 2>&1 &" if restart else ""
        else:
            dest_file = (
                os.path.join(target_bundle, os.path.basename(src_entry))
                if os.path.isdir(target_bundle)
                else target_bundle
            )
            replace_cmd = (
                f"mkdir -p {q(os.path.dirname(dest_file))} && "
                f"cp -f {q(src_entry)} {q(dest_file)} && "
                f"chmod +x {q(dest_file)}"
            )
            relaunch_cmd = f"nohup {q(dest_file)} >/dev/null 2>&1 &" if restart else ""

        wait_block = ""
        if int(pid) > 0:
            wait_block = (
                f"PID={int(pid)}\n"
                "TRIES=0\n"
                "while kill -0 \"$PID\" 2>/dev/null && [ \"$TRIES\" -lt 50 ]; do\n"
                "  sleep 0.2\n"
                "  TRIES=$((TRIES + 1))\n"
                "done\n"
            )

        script_content = (
            "#!/bin/sh\n"
            f"{wait_block}"
            f"{replace_cmd}\n"
            f"rm -rf {q(staged_root)}\n"
            f"{relaunch_cmd}\n"
            "rm -f \"$0\"\n"
        )
        fd, script_path = tempfile.mkstemp(prefix="speedview_updater_", suffix=".sh")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR)
        return script_path