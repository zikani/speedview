import json
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
    DEFAULT_RELEASES_API_URL,
    DEFAULT_RELEASES_PAGE_URL,
    DEFAULT_UPDATE_URL,
    RELEASE_HISTORY,
    RELEASES_CACHE_FILE,
    UPDATE_CHECK_INTERVAL_SECONDS,
)


def _safe_parse_version(ver_str):
    cleaned = str(ver_str or "").lstrip("v").strip()
    if not cleaned:
        return version.Version("0.0.0")
    try:
        return version.parse(cleaned)
    except Exception:
        return version.Version("0.0.0")


class UpdateChecker:
    """
    Cross-platform GitHub Release auto-updater (Windows, macOS, Linux).

    Enforces a 3-day check cooldown via settings.last_update_check to avoid
    GitHub API rate limits, downloads .zip release assets into a temp folder,
    extracts safely, and launches a detached helper script so the running app
    can exit, replace its files/folder cleanly, and restart.
    """

    def __init__(self, settings=None, check_interval=UPDATE_CHECK_INTERVAL_SECONDS, releases_cache_file=None):
        self.settings = settings
        self.check_interval = int(check_interval)
        self.current_version = APP_VERSION
        if settings and getattr(settings, 'update_url', None):
            self.github_api_url = settings.update_url
        else:
            self.github_api_url = DEFAULT_UPDATE_URL
        self.releases_api_url = self._derive_releases_api_url(self.github_api_url)
        self.releases_cache_file = releases_cache_file or RELEASES_CACHE_FILE

        self.update_available = False
        self.latest_version = None
        self.release_notes = None
        self.download_url = None
        self.asset_name = None
        self.release_page_url = DEFAULT_RELEASES_PAGE_URL
        self.source_zip_url = None
        self.all_releases = []
        self.staged_dir = None
        self.extracted_dir = None
        self.last_helper_script = None
        self.last_helper_process = None

    @staticmethod
    def _derive_releases_api_url(api_url):
        url = (api_url or DEFAULT_UPDATE_URL).rstrip("/")
        if url.endswith("/releases/latest"):
            return url[:-len("/latest")]
        if url.endswith("/releases"):
            return url
        if url == DEFAULT_UPDATE_URL.rstrip("/"):
            return DEFAULT_RELEASES_API_URL
        return None

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

    def _load_cached_releases(self):
        """Load previously fetched GitHub releases from disk cache."""
        if not self.releases_cache_file or not os.path.isfile(self.releases_cache_file):
            return []
        try:
            with open(self.releases_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict) and item.get("version")]
        except Exception:
            pass
        return []

    def _save_cached_releases(self, releases):
        """Persist normalized GitHub release records atomically for offline changelog viewing."""
        if not self.releases_cache_file:
            return
        try:
            cache_dir = os.path.dirname(self.releases_cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            tmp_file = self.releases_cache_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(releases, f, indent=2)
            os.replace(tmp_file, self.releases_cache_file)
        except Exception as e:
            print(f"Could not save releases cache: {e}")

    @staticmethod
    def _normalize_github_release(item):
        if not isinstance(item, dict):
            return None
        tag = str(item.get("tag_name") or item.get("version") or "").lstrip("v").strip()
        if not tag:
            return None
        published_at = str(item.get("published_at") or item.get("date") or "")
        date_str = published_at[:10] if len(published_at) >= 10 else published_at
        return {
            "version": tag,
            "date": date_str,
            "title": str(item.get("name") or "").strip(),
            "body": str(item.get("body") or "").strip(),
            "html_url": item.get("html_url") or DEFAULT_RELEASES_PAGE_URL,
            "zipball_url": item.get("zipball_url"),
            "assets": item.get("assets") or [],
            "features": list(item.get("features") or []),
            "changes": list(item.get("changes") or []),
        }

    def _merge_releases(self, remote_releases=None, include_builtin=True):
        """Merge remote/cached releases with built-in RELEASE_HISTORY newest-first without losing detail."""
        merged = {}

        if include_builtin:
            for entry in RELEASE_HISTORY:
                ver = str(entry.get("version", "")).lstrip("v").strip()
                if not ver:
                    continue
                merged[ver] = {
                    "version": ver,
                    "date": entry.get("date", ""),
                    "title": entry.get("title", ""),
                    "features": list(entry.get("features") or []),
                    "changes": list(entry.get("changes") or []),
                    "body": "",
                    "html_url": DEFAULT_RELEASES_PAGE_URL,
                }

        for source_list in (self._load_cached_releases(), remote_releases or []):
            for raw in source_list:
                norm = self._normalize_github_release(raw)
                if not norm:
                    continue
                ver = norm["version"]
                existing = merged.get(ver)
                if existing:
                    if norm.get("date") and not existing.get("date"):
                        existing["date"] = norm["date"]
                    if norm.get("title"):
                        existing["title"] = norm["title"]
                    if norm.get("body"):
                        existing["body"] = norm["body"]
                    if norm.get("features"):
                        existing["features"] = norm["features"]
                    if norm.get("changes"):
                        existing["changes"] = norm["changes"]
                    if norm.get("html_url"):
                        existing["html_url"] = norm["html_url"]
                else:
                    merged[ver] = norm

        ordered = sorted(
            merged.values(),
            key=lambda item: _safe_parse_version(item.get("version")),
            reverse=True,
        )
        return ordered

    @staticmethod
    def format_release_entry_markdown(entry):
        """Format one release record (features + changelog / release notes) as clean Markdown."""
        ver = str(entry.get("version", "")).lstrip("v").strip()
        title = str(entry.get("title") or "").strip()
        date_str = str(entry.get("date") or "").strip()
        heading = f"## v{ver}"
        if title and title.lower() not in (f"v{ver}".lower(), ver.lower()):
            heading += f" — {title}"
        if date_str:
            heading += f" ({date_str})"

        lines = [heading]
        features = entry.get("features") or []
        changes = entry.get("changes") or []
        body = (entry.get("body") or "").strip()

        if features:
            lines.append("### Features")
            lines.extend(f"- {feat}" for feat in features)

        if changes:
            lines.append("### Changelog")
            lines.extend(f"- {chg}" for chg in changes)
        elif body:
            lines.append(body)
        elif not features:
            lines.append("- Maintenance and stability improvements")

        return "\n".join(lines)

    def get_all_changelogs_markdown(self, since_version=None, include_builtin=True, releases=None):
        """Return combined Markdown of all released versions' features and changelogs."""
        records = self._merge_releases(releases, include_builtin=include_builtin)
        if since_version:
            base_ver = _safe_parse_version(since_version)
            records = [r for r in records if _safe_parse_version(r.get("version")) > base_ver]
        if not records:
            return "No release changelog entries available."
        return "\n\n".join(self.format_release_entry_markdown(r) for r in records)

    def fetch_all_releases(self, force=False):
        """Fetch all GitHub releases (or cached/fallback single release) and cache them."""
        cached = self._load_cached_releases()
        if not self.should_check_for_updates(force=force) and cached:
            self.all_releases = self._merge_releases(cached, include_builtin=True)
            return self.all_releases

        headers = {
            "User-Agent": f"SpeedView/{self.current_version}",
            "Accept": "application/vnd.github+json",
        }
        fetched_raw = []
        endpoints = []
        if self.releases_api_url:
            sep = "&" if "?" in self.releases_api_url else "?"
            endpoints.append(f"{self.releases_api_url}{sep}per_page=30")
        if self.github_api_url and self.github_api_url not in endpoints:
            endpoints.append(self.github_api_url)

        for url in endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, list):
                    fetched_raw = [r for r in payload if not r.get("draft")]
                    break
                if isinstance(payload, dict) and payload.get("tag_name"):
                    fetched_raw = [payload]
                    break
            except Exception as e:
                print(f"Release history fetch failed for {url}: {e}")

        if fetched_raw:
            normalized = []
            for item in fetched_raw:
                norm = self._normalize_github_release(item)
                if norm:
                    normalized.append(norm)
            if normalized:
                self._save_cached_releases(normalized)
                self.all_releases = self._merge_releases(normalized, include_builtin=True)
                return self.all_releases

        self.all_releases = self._merge_releases(cached, include_builtin=True)
        return self.all_releases

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

        headers = {
            "User-Agent": f"SpeedView/{self.current_version}",
            "Accept": "application/vnd.github+json",
        }

        try:
            response = requests.get(self.github_api_url, headers=headers, timeout=10)
            self._record_check_timestamp()

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                print(f"Update check HTTP error: {http_err}")
                self.all_releases = self._merge_releases(include_builtin=True)
                if not self.release_notes:
                    self.release_notes = self.get_all_changelogs_markdown(include_builtin=True)
                return False

            raw_json = response.json()
            raw_list = []
            latest_data = None

            if isinstance(raw_json, list):
                raw_list = [r for r in raw_json if isinstance(r, dict) and not r.get("draft")]
                if raw_list:
                    raw_list.sort(key=lambda r: _safe_parse_version(r.get("tag_name")), reverse=True)
                    latest_data = raw_list[0]
            elif isinstance(raw_json, dict):
                latest_data = raw_json
                raw_list = [raw_json]
                # Opportunistically fetch full release history if configured URL is GitHub /releases/latest
                if self.releases_api_url and self.releases_api_url != self.github_api_url.rstrip("/"):
                    try:
                        sep = "&" if "?" in self.releases_api_url else "?"
                        hist_resp = requests.get(
                            f"{self.releases_api_url}{sep}per_page=30",
                            headers=headers,
                            timeout=8,
                        )
                        if hist_resp.ok and isinstance(hist_resp.json(), list):
                            hist_items = [r for r in hist_resp.json() if isinstance(r, dict) and not r.get("draft")]
                            if hist_items:
                                raw_list = hist_items
                    except Exception:
                        pass

            if not latest_data:
                self.all_releases = self._merge_releases(include_builtin=True)
                self.release_notes = self.get_all_changelogs_markdown(include_builtin=True)
                return False

            normalized_remote = [
                n for n in (self._normalize_github_release(item) for item in raw_list) if n is not None
            ]
            if normalized_remote:
                self._save_cached_releases(normalized_remote)

            self.all_releases = self._merge_releases(normalized_remote, include_builtin=True)
            self.latest_version = str(latest_data.get('tag_name', '')).lstrip('v').strip()
            self.release_page_url = latest_data.get('html_url') or DEFAULT_RELEASES_PAGE_URL
            self.source_zip_url = latest_data.get('zipball_url')

            if self.latest_version and _safe_parse_version(self.latest_version) > _safe_parse_version(self.current_version):
                self.update_available = True
                newer_notes = self.get_all_changelogs_markdown(
                    since_version=self.current_version,
                    include_builtin=False,
                    releases=normalized_remote,
                )
                if newer_notes and "No release changelog" not in newer_notes:
                    self.release_notes = newer_notes
                else:
                    self.release_notes = latest_data.get('body') or 'No release notes available'

                asset_url, asset_name = self._select_asset_for_platform(latest_data.get('assets', []))
                if not getattr(sys, 'frozen', False) and self.source_zip_url:
                    self.download_url = self.source_zip_url
                    self.asset_name = f"SpeedView-{self.latest_version}-source.zip"
                elif asset_url:
                    self.download_url = asset_url
                    self.asset_name = asset_name
                elif self.source_zip_url:
                    self.download_url = self.source_zip_url
                    self.asset_name = f"SpeedView-{self.latest_version}-source.zip"
                else:
                    self.download_url = self.release_page_url
            else:
                self.release_notes = self.get_all_changelogs_markdown(
                    include_builtin=True,
                    releases=normalized_remote,
                )
            return self.update_available
        except Exception as e:
            print(f"Update check failed: {e}")
            self.all_releases = self._merge_releases(include_builtin=True)
            if not self.release_notes:
                self.release_notes = self.get_all_changelogs_markdown(include_builtin=True)
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

    def download_update(self, progress_callback=None, bytes_callback=None):
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
                        if bytes_callback:
                            bytes_callback(downloaded, total_size)
                        if progress_callback:
                            if total_size > 0:
                                progress_callback(min(100.0, (downloaded / total_size) * 100.0))
                            else:
                                progress_callback(-1.0)

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

    @staticmethod
    def _get_project_root():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    @staticmethod
    def _contains_source_entrypoint(path):
        if not path or not os.path.isdir(path):
            return False
        if os.path.isfile(os.path.join(path, "main.py")) and os.path.isdir(os.path.join(path, "speedview")):
            return True
        entries = os.listdir(path)
        if len(entries) == 1:
            inner = os.path.join(path, entries[0])
            return os.path.isfile(os.path.join(inner, "main.py")) and os.path.isdir(os.path.join(inner, "speedview"))
        return False

    @staticmethod
    def _is_onedir_bundle(path):
        """Return True when directory holds a PyInstaller onedir layout (exe + _internal/libs)."""
        if not path or not os.path.isdir(path):
            return False
        entries = os.listdir(path)
        if "_internal" in entries and os.path.isdir(os.path.join(path, "_internal")):
            return True
        has_binary = any(
            name.endswith(".exe") or name in ("SpeedView", "SpeedView-linux-x64")
            for name in entries
        )
        return has_binary and len(entries) > 1

    def can_self_replace(self, target_path=None):
        """Return True when a valid frozen executable, explicit target, or source checkout can be updated."""
        if target_path or getattr(sys, 'frozen', False):
            return True
        return os.path.isfile(os.path.join(self._get_project_root(), "main.py"))

    @staticmethod
    def _resolve_python_executable():
        """Return a Python interpreter executable suitable for launching the updater subprocess."""
        if not getattr(sys, 'frozen', False) and sys.executable:
            return sys.executable
        return shutil.which("python3") or shutil.which("python")

    @staticmethod
    def _is_dir_writable(path):
        target_dir = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(target_dir):
            return True
        return os.access(target_dir, os.W_OK)

    @staticmethod
    def _launch_elevated_windows(executable, arguments=""):
        """Prompt UAC elevation on Windows when updating protected directories like Program Files."""
        try:
            import ctypes
            rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, arguments, None, 1)
            return int(rc) > 32
        except Exception as e:
            print(f"Windows elevated updater launch failed: {e}")
            return False

    def install_update(self, update_file, target_path=None, restart=True, launch_script=True, wait_pid=None):
        """
        Spawn a detached Python helper subprocess (or shell fallback if frozen without system Python)
        that waits for the running process to exit, replaces the old executable/onedir/bundle
        from the temp staging directory, cleans up temp files, and restarts the updated app.
        """
        try:
            if not update_file or not os.path.exists(update_file):
                raise FileNotFoundError(f"Update artifact not found: {update_file}")

            if not self.can_self_replace(target_path):
                return False

            payload_path, staged_root, _ = self._resolve_payload(update_file)
            is_source_run = not target_path and not getattr(sys, 'frozen', False)
            if target_path:
                resolved_target = target_path
            elif getattr(sys, 'frozen', False):
                resolved_target = sys.executable
            else:
                resolved_target = self._get_project_root()

            pid_to_wait = os.getpid() if wait_pid is None else int(wait_pid)
            python_exe = self._resolve_python_executable()
            system = platform.system()
            needs_windows_elevation = (
                system == "Windows"
                and launch_script
                and not self._is_dir_writable(resolved_target)
            )

            if python_exe:
                script_path = self._create_python_updater_script(
                    payload_path=payload_path,
                    staged_root=staged_root,
                    target_path=resolved_target,
                    pid=pid_to_wait,
                    restart=restart,
                    source_run=is_source_run,
                )
                self.last_helper_script = script_path
                if launch_script:
                    if needs_windows_elevation:
                        return self._launch_elevated_windows(python_exe, f'"{script_path}"')
                    kwargs = {"close_fds": True}
                    if system == "Windows":
                        kwargs["creationflags"] = (
                            getattr(subprocess, "CREATE_NO_WINDOW", 0)
                            | getattr(subprocess, "DETACHED_PROCESS", 0)
                            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                        )
                    else:
                        kwargs["start_new_session"] = True
                        kwargs["stdin"] = subprocess.DEVNULL
                        kwargs["stdout"] = subprocess.DEVNULL
                        kwargs["stderr"] = subprocess.DEVNULL
                    self.last_helper_process = subprocess.Popen([python_exe, script_path], **kwargs)
                return True

            if system == "Windows":
                script_path = self._create_windows_updater_script(
                    payload_path=payload_path,
                    staged_root=staged_root,
                    target_path=resolved_target,
                    pid=pid_to_wait,
                    restart=restart,
                    source_run=is_source_run,
                )
                self.last_helper_script = script_path
                if launch_script:
                    if needs_windows_elevation:
                        return self._launch_elevated_windows("cmd.exe", f'/c "{script_path}"')
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
                source_run=is_source_run,
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
    def _find_relaunch_binary(dest_dir, preferred_name):
        for candidate in (preferred_name, "SpeedView.exe", "SpeedView", "SpeedView-linux-x64"):
            if not candidate:
                continue
            full = os.path.join(dest_dir, candidate)
            if os.path.isfile(full):
                return full
        return os.path.join(dest_dir, preferred_name) if preferred_name else dest_dir

    def _create_python_updater_script(
        self, payload_path, staged_root, target_path, pid, restart=True, source_run=False
    ):
        """Create a cross-platform Python helper script to wait for PID, swap files/onedir, clean temp dir, and restart."""
        target_bundle = self._find_app_bundle_or_binary(target_path)
        target_abs = os.path.abspath(target_bundle)
        target_name = os.path.basename(target_abs)
        src_entry = self._pick_source_entry(payload_path, target_name)

        is_app_bundle = False
        if (target_abs.endswith('.app') and src_entry.endswith('.app')) or (
            os.path.isdir(src_entry) and src_entry.endswith('.app')
        ):
            is_app_bundle = True
            dest_path = target_abs if target_abs.endswith('.app') else os.path.join(target_abs, os.path.basename(src_entry))
            relaunch_args = ["open", "-n", dest_path] if restart else []
        elif os.path.isdir(src_entry):
            dest_path = target_abs if os.path.isdir(target_abs) else os.path.dirname(target_abs)
            if not restart:
                relaunch_args = []
            elif source_run and os.path.isfile(os.path.join(src_entry, "main.py")):
                relaunch_args = [sys.executable, os.path.join(dest_path, "main.py")]
            else:
                relaunch_target = (
                    target_abs
                    if os.path.isfile(target_abs)
                    else self._find_relaunch_binary(dest_path, target_name)
                )
                relaunch_args = [relaunch_target]
        else:
            dest_path = (
                os.path.join(target_abs, os.path.basename(src_entry))
                if os.path.isdir(target_abs)
                else target_abs
            )
            relaunch_args = [dest_path] if restart else []

        script_lines = [
            "import os",
            "import shutil",
            "import stat",
            "import subprocess",
            "import time",
            "",
            f"PID = {int(pid)}",
            f"SRC_ENTRY = {repr(os.path.abspath(src_entry))}",
            f"DEST_PATH = {repr(dest_path)}",
            f"STAGED_ROOT = {repr(os.path.abspath(staged_root))}",
            f"RELAUNCH_ARGS = {repr(relaunch_args)}",
            f"IS_APP_BUNDLE = {repr(is_app_bundle)}",
            "IS_WINDOWS = os.name == 'nt'",
            "",
            "def wait_for_exit(pid):",
            "    if pid <= 0:",
            "        return",
            "    for _ in range(100):",
            "        try:",
            "            if IS_WINDOWS:",
            "                import ctypes",
            "                h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)",
            "                if not h:",
            "                    break",
            "                res = ctypes.windll.kernel32.WaitForSingleObject(h, 200)",
            "                ctypes.windll.kernel32.CloseHandle(h)",
            "                if res == 0:",
            "                    break",
            "            else:",
            "                os.kill(pid, 0)",
            "                time.sleep(0.2)",
            "        except OSError:",
            "            break",
            "        except Exception:",
            "            break",
            "",
            "wait_for_exit(PID)",
            "",
            "try:",
            "    if IS_APP_BUNDLE and os.path.isdir(SRC_ENTRY):",
            "        if os.path.exists(DEST_PATH):",
            "            shutil.rmtree(DEST_PATH, ignore_errors=True)",
            "        shutil.copytree(SRC_ENTRY, DEST_PATH, dirs_exist_ok=True)",
            "    elif os.path.isdir(SRC_ENTRY):",
            "        os.makedirs(DEST_PATH, exist_ok=True)",
            "        shutil.copytree(SRC_ENTRY, DEST_PATH, dirs_exist_ok=True)",
            "        if not IS_WINDOWS:",
            "            for root, _dirs, files in os.walk(DEST_PATH):",
            "                for fname in files:",
            "                    if fname in ('SpeedView', 'SpeedView-linux-x64'):",
            "                        fpath = os.path.join(root, fname)",
            "                        os.chmod(fpath, os.stat(fpath).st_mode | stat.S_IXUSR)",
            "    else:",
            "        os.makedirs(os.path.dirname(DEST_PATH), exist_ok=True)",
            "        shutil.copy2(SRC_ENTRY, DEST_PATH)",
            "        if not IS_WINDOWS:",
            "            os.chmod(DEST_PATH, os.stat(DEST_PATH).st_mode | stat.S_IXUSR)",
            "finally:",
            "    if STAGED_ROOT and os.path.exists(STAGED_ROOT):",
            "        shutil.rmtree(STAGED_ROOT, ignore_errors=True)",
            "",
            "if RELAUNCH_ARGS:",
            "    kwargs = {'close_fds': True}",
            "    if IS_WINDOWS:",
            "        kwargs['creationflags'] = (",
            "            getattr(subprocess, 'DETACHED_PROCESS', 0)",
            "            | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)",
            "        )",
            "    else:",
            "        kwargs['start_new_session'] = True",
            "        kwargs['stdin'] = subprocess.DEVNULL",
            "        kwargs['stdout'] = subprocess.DEVNULL",
            "        kwargs['stderr'] = subprocess.DEVNULL",
            "    subprocess.Popen(RELAUNCH_ARGS, **kwargs)",
            "",
            "try:",
            "    os.remove(__file__)",
            "except OSError:",
            "    pass",
            "",
        ]

        fd, script_path = tempfile.mkstemp(prefix="speedview_updater_", suffix=".py")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(script_lines))
        return script_path

    @staticmethod
    def _pick_source_entry(payload_path, target_basename):
        """Pick the matching file, onedir directory, .app, or unwrapped root inside extracted payload."""
        if os.path.isfile(payload_path):
            return payload_path
        entries = os.listdir(payload_path)
        if not entries:
            return payload_path

        # Unwrap single top-level directory (e.g. SpeedView/SpeedView.exe + SpeedView/_internal/)
        if len(entries) == 1:
            only_path = os.path.join(payload_path, entries[0])
            if os.path.isdir(only_path):
                if only_path.endswith(".app"):
                    return only_path
                return only_path
            return only_path

        # Multi-entry folder: if it is an onedir bundle (e.g. SpeedView.exe + _internal/), return the directory
        if UpdateChecker._is_onedir_bundle(payload_path):
            return payload_path

        for name in entries:
            if name == target_basename:
                return os.path.join(payload_path, name)
        for name in entries:
            if name.endswith(('.exe', '.app')):
                return os.path.join(payload_path, name)
        return payload_path

    def _create_windows_updater_script(
        self, payload_path, staged_root, target_path, pid, restart=True, source_run=False
    ):
        target_abs = os.path.abspath(target_path)
        target_dir = target_abs if os.path.isdir(target_abs) else os.path.dirname(target_abs)
        target_name = os.path.basename(target_abs)
        src_entry = self._pick_source_entry(payload_path, target_name)

        if os.path.isdir(src_entry):
            replace_block = f'xcopy "{src_entry}\\*" "{target_dir}\\" /E /Y /I /Q > nul'
            if source_run and os.path.isfile(os.path.join(src_entry, "main.py")):
                restart_cmd = f'start "" "{sys.executable}" "{os.path.join(target_dir, "main.py")}"'
            else:
                restart_exe = (
                    target_abs
                    if os.path.isfile(target_abs)
                    else self._find_relaunch_binary(target_dir, target_name)
                )
                restart_cmd = f'start "" "{restart_exe}"'
        else:
            dest_file = target_abs if not os.path.isdir(target_abs) else os.path.join(target_dir, os.path.basename(src_entry))
            replace_block = f'copy /Y "{src_entry}" "{dest_file}" > nul'
            restart_cmd = f'start "" "{dest_file}"'

        restart_block = restart_cmd if restart else ''
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

    def _create_posix_updater_script(
        self, payload_path, staged_root, target_path, pid, restart=True, source_run=False
    ):
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
        elif os.path.isdir(src_entry) and src_entry.endswith('.app'):
            dest_app = target_bundle if target_bundle.endswith('.app') else os.path.join(target_bundle, os.path.basename(src_entry))
            replace_cmd = f"rm -rf {q(dest_app)} && cp -Rf {q(src_entry)} {q(dest_app)}"
            relaunch_cmd = f"open -n {q(dest_app)}" if restart else ""
        elif os.path.isdir(src_entry):
            target_dir = target_bundle if os.path.isdir(target_bundle) else os.path.dirname(target_bundle)
            replace_cmd = f"mkdir -p {q(target_dir)} && cp -Rf {q(src_entry)}/. {q(target_dir)}/"
            if source_run and os.path.isfile(os.path.join(src_entry, "main.py")):
                relaunch_cmd = f"nohup {q(sys.executable)} {q(os.path.join(target_dir, 'main.py'))} >/dev/null 2>&1 &" if restart else ""
            else:
                relaunch_target = (
                    target_bundle
                    if os.path.isfile(target_bundle)
                    else self._find_relaunch_binary(target_dir, target_name)
                )
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