import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
import requests
import psutil
from PyQt5.QtCore import QObject, pyqtSignal


class _ChunkedUploadReader:
    """File-like stream wrapper that generates payload chunks and reports real-time upload speed."""

    def __init__(self, total_bytes, chunk_size=65536, on_progress=None):
        self.total_bytes = int(total_bytes)
        self.chunk_size = int(chunk_size)
        self.bytes_sent = 0
        self.on_progress = on_progress
        self._chunk = b"\x55" * self.chunk_size
        self._start_time = None
        self._last_report = 0.0

    def __len__(self):
        return self.total_bytes

    def read(self, size=-1):
        if self._start_time is None:
            self._start_time = time.perf_counter()
        remaining = self.total_bytes - self.bytes_sent
        if remaining <= 0:
            return b""
        to_send = remaining if (size is None or size < 0) else min(size, remaining)
        if to_send == self.chunk_size:
            data = self._chunk
        elif to_send < self.chunk_size:
            data = self._chunk[:to_send]
        else:
            data = b"\x55" * to_send
        self.bytes_sent += len(data)

        now = time.perf_counter()
        elapsed = max(1e-6, now - self._start_time)
        if self.on_progress and (now - self._last_report >= 0.12 or self.bytes_sent == self.total_bytes):
            self._last_report = now
            mbps = (self.bytes_sent * 8.0) / (elapsed * 1_000_000.0)
            self.on_progress(self.bytes_sent, mbps)
        return data


class NetworkController(QObject):
    """Handles network connectivity, real interface detection, and speed testing"""

    connection_updated = pyqtSignal(str, int)  # status, signal_strength
    signal_strength_updated = pyqtSignal(int)  # signal_strength (0-100)
    latency_updated = pyqtSignal(object)  # latency_ms (int or None)
    speed_test_progress = pyqtSignal(str, float, float)  # status, download_mbps, upload_mbps
    speed_test_complete = pyqtSignal(float, float)  # download_speed, upload_speed
    speed_test_failed = pyqtSignal(str)  # error_message

    DEFAULT_DOWNLOAD_URLS = (
        "https://speed.cloudflare.com/__down?bytes=10000000",
        "https://proof.ovh.net/files/10Mb.dat",
        "https://ash-speed.hetzner.com/10MB.bin",
    )
    DEFAULT_UPLOAD_URLS = (
        "https://speed.cloudflare.com/__up",
        "https://httpbin.org/post",
    )

    def __init__(self, selected_interface=None):
        super().__init__()
        self.selected_interface = selected_interface
        self.connection_status = "Checking..."
        self.signal_strength = 0
        self.latency_ms = None
        self.interface_details = {}
        self.updating = False
        self.testing = False

    def set_interface(self, interface_name):
        """Set preferred network interface for status/detail inspection."""
        self.selected_interface = interface_name
        self.interface_details = {}
        self.check_connection_status()

    def get_cached_interface_details(self, interface_name=None):
        """Return cached interface details if available, else compute and cache."""
        target = interface_name if interface_name is not None else self.selected_interface
        if self.interface_details and (target is None or self.interface_details.get("interface") == target):
            return self.interface_details
        self.interface_details = self.get_interface_details(target)
        return self.interface_details

    def check_connection_status(self):
        """Check if network is connected in a background thread"""
        try:
            if self.updating:
                return
            self.updating = True
            thread = threading.Thread(target=self._check_connection_thread, daemon=True)
            thread.start()
        except Exception as e:
            print(f"Error checking connection: {e}")
            self.updating = False

    def _check_connection_thread(self):
        """Thread to check connection status, real-time ping latency, and interface details"""
        status = "Disconnected"
        latency_ms = None
        for host in ("8.8.8.8", "1.1.1.1"):
            try:
                t0 = time.perf_counter()
                with socket.create_connection((host, 53), timeout=3):
                    t1 = time.perf_counter()
                status = "Connected"
                latency_ms = max(1, int(round((t1 - t0) * 1000.0)))
                break
            except (TimeoutError, OSError):
                continue
            except Exception as e:
                print(f"Unexpected error during network check: {e}")
                continue

        details = self.get_interface_details(self.selected_interface, connected=(status == "Connected"))
        strength = details.get("signal_strength", 0)
        latency_changed = latency_ms != self.latency_ms

        changed = (
            status != self.connection_status
            or strength != self.signal_strength
            or details != self.interface_details
            or latency_changed
        )
        self.interface_details = details
        self.latency_ms = latency_ms

        if latency_changed and hasattr(self, "latency_updated") and hasattr(self.latency_updated, "emit"):
            self.latency_updated.emit(latency_ms)

        if changed:
            self.connection_status = status
            self.signal_strength = strength
            if hasattr(self.connection_updated, "emit"):
                self.connection_updated.emit(status, strength)
            if hasattr(self.signal_strength_updated, "emit"):
                self.signal_strength_updated.emit(strength)

        self.updating = False

    def _resolve_interface(self, interface_name=None):
        """Pick selected interface if active/available, else best non-loopback active interface."""
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
        except Exception:
            return None, None, []

        if interface_name and interface_name in stats:
            return interface_name, stats[interface_name], addrs.get(interface_name, [])

        # Prefer active non-loopback interface with an IPv4/IPv6 address
        candidates = []
        for iface, stat in stats.items():
            flags = (stat.flags or "").lower()
            if iface == "lo" or "loopback" in flags or "loopback" in iface.lower():
                continue
            if not stat.isup:
                continue
            iface_addrs = addrs.get(iface, [])
            has_ip = any(
                a.family in (socket.AF_INET, socket.AF_INET6) and not a.address.startswith("127.")
                for a in iface_addrs
            )
            candidates.append((has_ip, iface, stat, iface_addrs))

        if candidates:
            candidates.sort(key=lambda item: (not item[0], item[1]))
            _, iface, stat, iface_addrs = candidates[0]
            return iface, stat, iface_addrs

        # Fallback to any up interface
        for iface, stat in stats.items():
            if stat.isup:
                return iface, stat, addrs.get(iface, [])

        return None, None, []

    @staticmethod
    def _freq_to_band(freq_mhz):
        if not freq_mhz:
            return None
        try:
            freq = float(freq_mhz)
            if freq < 3000:
                return "2.4GHz"
            if freq < 5900:
                return "5GHz"
            return "6GHz"
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _channel_to_band(channel):
        try:
            ch = int(channel)
            if 1 <= ch <= 14:
                return "2.4GHz"
            if 32 <= ch <= 177:
                return "5GHz"
            if ch > 177:
                return "6GHz"
        except (TypeError, ValueError):
            pass
        return None

    def _detect_wifi_linux(self, iface):
        """Detect real Wi-Fi SSID, band, and signal percentage on Linux."""
        is_wifi = False
        ssid = None
        band = None
        signal_pct = None

        if iface and os.path.exists(f"/sys/class/net/{iface}/wireless"):
            is_wifi = True

        # Read /proc/net/wireless for signal quality
        try:
            with open('/proc/net/wireless', 'r') as f:
                for line in f:
                    if ":" in line and not line.startswith("Inter"):
                        if_name = line.split(":", 1)[0].strip()
                        if iface and if_name != iface:
                            continue
                        is_wifi = True
                        parts = line.split(":", 1)[1].split()
                        if len(parts) >= 2:
                            quality = float(parts[1].rstrip('.'))
                            signal_pct = max(0, min(100, int(quality * 100 / 70)))
                        break
        except Exception:
            pass

        if not is_wifi and not ("wl" in (iface or "").lower() or "wi-fi" in (iface or "").lower() or "wifi" in (iface or "").lower()):
            return False, None, None, None

        # Try iwgetid for SSID and frequency
        if shutil.which("iwgetid") and iface:
            try:
                out = subprocess.check_output(["iwgetid", iface, "-r"], stderr=subprocess.DEVNULL, timeout=2).decode().strip()
                if out:
                    ssid = out
                    is_wifi = True
            except Exception:
                pass
            try:
                freq_out = subprocess.check_output(["iwgetid", iface, "-f", "-r"], stderr=subprocess.DEVNULL, timeout=2).decode().strip()
                if freq_out:
                    # Output in Hz (e.g., 5180000000) or GHz
                    val = float(freq_out)
                    mhz = val / 1_000_000 if val > 100_000 else (val * 1000 if val < 100 else val)
                    band = self._freq_to_band(mhz)
            except Exception:
                pass

        # Try iw dev <iface> link
        if shutil.which("iw") and iface and (not ssid or not band or signal_pct is None):
            try:
                out = subprocess.check_output(["iw", "dev", iface, "link"], stderr=subprocess.DEVNULL, timeout=2).decode()
                if "Connected to" in out:
                    is_wifi = True
                    m_ssid = re.search(r"SSID:\s*(.+)", out)
                    if m_ssid and not ssid:
                        ssid = m_ssid.group(1).strip()
                    m_freq = re.search(r"freq:\s*(\d+)", out)
                    if m_freq and not band:
                        band = self._freq_to_band(m_freq.group(1))
                    m_sig = re.search(r"signal:\s*(-\d+)\s*dBm", out)
                    if m_sig and signal_pct is None:
                        dbm = int(m_sig.group(1))
                        signal_pct = max(0, min(100, 2 * (dbm + 100)))
            except Exception:
                pass

        # Try nmcli as fallback
        if shutil.which("nmcli") and (not ssid or not band or signal_pct is None):
            try:
                out = subprocess.check_output(
                    ["nmcli", "-t", "-f", "ACTIVE,SSID,FREQ,SIGNAL,DEVICE", "dev", "wifi"],
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                ).decode()
                for line in out.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 5 and parts[0] == "yes":
                        if not iface or parts[4] == iface:
                            is_wifi = True
                            ssid = ssid or (parts[1] or None)
                            freq_match = re.search(r"(\d+)", parts[2])
                            if freq_match and not band:
                                band = self._freq_to_band(freq_match.group(1))
                            if parts[3].isdigit() and signal_pct is None:
                                signal_pct = int(parts[3])
                            break
            except Exception:
                pass

        return is_wifi, ssid, band, signal_pct

    def _detect_wifi_windows(self, iface):
        """Detect real Wi-Fi SSID, band, and signal percentage on Windows."""
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            out = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                stderr=subprocess.DEVNULL,
                timeout=3,
                creationflags=creationflags,
            ).decode("utf-8", errors="ignore")
        except Exception:
            return False, None, None, None

        # Split blocks by "Name"
        blocks = re.split(r"\r?\n\s*\r?\n", out)
        for block in blocks:
            name_m = re.search(r"^\s*Name\s*:\s*(.+)$", block, re.MULTILINE)
            if not name_m:
                continue
            block_iface = name_m.group(1).strip()
            if iface and block_iface.lower() != iface.lower():
                continue
            state_m = re.search(r"^\s*State\s*:\s*(.+)$", block, re.MULTILINE)
            if state_m and "connected" not in state_m.group(1).lower():
                return True, None, None, 0

            ssid_m = re.search(r"^\s*SSID\s*:\s*(.+)$", block, re.MULTILINE)
            sig_m = re.search(r"^\s*Signal\s*:\s*(\d+)%", block, re.MULTILINE)
            band_m = re.search(r"^\s*Band\s*:\s*(.+)$", block, re.MULTILINE)
            chan_m = re.search(r"^\s*Channel\s*:\s*(\d+)", block, re.MULTILINE)
            radio_m = re.search(r"^\s*Radio type\s*:\s*(.+)$", block, re.MULTILINE)

            ssid = ssid_m.group(1).strip() if ssid_m else None
            sig = int(sig_m.group(1)) if sig_m else None
            band = None
            if band_m:
                raw_band = band_m.group(1).strip()
                if "5" in raw_band:
                    band = "5GHz"
                elif "2.4" in raw_band:
                    band = "2.4GHz"
                elif "6" in raw_band:
                    band = "6GHz"
            if not band and chan_m:
                band = self._channel_to_band(chan_m.group(1))
            if not band and radio_m:
                radio = radio_m.group(1).lower()
                if "802.11a" in radio or "802.11ac" in radio:
                    band = "5GHz"
                elif "802.11b" in radio or "802.11g" in radio:
                    band = "2.4GHz"
            return True, ssid, band, sig

        return False, None, None, None

    def _detect_wifi_macos(self, iface):
        """Detect real Wi-Fi SSID, band, and signal percentage on macOS."""
        airport_cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.exists(airport_cmd):
            return False, None, None, None
        try:
            out = subprocess.check_output([airport_cmd, "-I"], stderr=subprocess.DEVNULL, timeout=2).decode("utf-8", errors="ignore")
            if not out.strip() or "AirPort: Off" in out:
                return False, None, None, None
            ssid_m = re.search(r"^\s*SSID:\s*(.+)$", out, re.MULTILINE)
            rssi_m = re.search(r"agrCtlRSSI:\s*(-\d+)", out)
            chan_m = re.search(r"channel:\s*(\d+)", out)
            ssid = ssid_m.group(1).strip() if ssid_m else None
            sig = max(0, min(100, 2 * (int(rssi_m.group(1)) + 100))) if rssi_m else None
            band = self._channel_to_band(chan_m.group(1)) if chan_m else None
            return True, ssid, band, sig
        except Exception:
            return False, None, None, None

    def _get_link_speed(self, iface, stat):
        """Get real link speed in Mbps from psutil or Linux sysfs, or None if unavailable."""
        if stat and getattr(stat, "speed", 0) and stat.speed > 0:
            return int(stat.speed)
        if platform.system() == "Linux" and iface:
            try:
                with open(f"/sys/class/net/{iface}/speed", "r") as f:
                    val = int(f.read().strip())
                    if val > 0:
                        return val
            except Exception:
                pass
        return None

    def get_interface_details(self, interface_name=None, connected=None):
        """Return real detected details for the active or selected network interface."""
        target_iface = interface_name if interface_name is not None else self.selected_interface
        iface, stat, iface_addrs = self._resolve_interface(target_iface)

        if connected is None:
            connected = self.connection_status == "Connected"

        if not iface or not stat:
            return {
                "interface": None,
                "connection_type": "Disconnected",
                "ipv4": None,
                "ipv6": None,
                "link_speed_mbps": None,
                "ssid": None,
                "band": None,
                "signal_strength": 0,
                "summary": "No active interface",
            }

        ipv4 = None
        ipv6 = None
        for addr in iface_addrs:
            if addr.family == socket.AF_INET and not ipv4:
                ipv4 = addr.address
            elif addr.family == socket.AF_INET6 and not ipv6:
                ipv6 = addr.address.split("%")[0]

        link_speed = self._get_link_speed(iface, stat)
        flags = (stat.flags or "").lower()
        iface_lower = iface.lower()

        system = platform.system()
        is_wifi, ssid, band, wifi_signal = False, None, None, None
        if system == "Linux":
            is_wifi, ssid, band, wifi_signal = self._detect_wifi_linux(iface)
        elif system == "Windows":
            is_wifi, ssid, band, wifi_signal = self._detect_wifi_windows(iface)
        elif system == "Darwin":
            is_wifi, ssid, band, wifi_signal = self._detect_wifi_macos(iface)

        if not stat.isup:
            conn_type = "Disconnected"
        elif is_wifi:
            conn_type = "Wi-Fi"
        elif iface_lower == "lo" or "loopback" in flags:
            conn_type = "Loopback"
        elif any(k in iface_lower for k in ("veth", "docker", "virbr", "vmware", "virtual", "vethernet", "tun", "tap")):
            conn_type = "Virtual"
        else:
            conn_type = "Ethernet"

        if not stat.isup or not connected:
            signal_strength = 0
        elif is_wifi:
            signal_strength = wifi_signal if wifi_signal is not None else 0
        else:
            # Wired/active non-Wi-Fi link has full link signal when up and connected
            signal_strength = 100

        parts = []
        if ssid:
            parts.append(ssid)
        if band:
            parts.append(band)
        if link_speed:
            parts.append(f"{link_speed} Mbps")
        if ipv4:
            parts.append(ipv4)
        elif ipv6:
            parts.append(ipv6)
        if not parts:
            parts.append(iface)

        return {
            "interface": iface,
            "connection_type": conn_type,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "link_speed_mbps": link_speed,
            "ssid": ssid,
            "band": band,
            "signal_strength": signal_strength,
            "summary": " • ".join(parts),
        }

    def _get_signal_strength(self):
        """Return real signal strength (0-100) for current/selected interface."""
        details = self.get_interface_details(self.selected_interface, connected=True)
        return details.get("signal_strength", 0)

    def measure_file_speed(
        self,
        download_urls=None,
        upload_urls=None,
        upload_size_bytes=2 * 1024 * 1024,
        chunk_size=65536,
        timeout=12,
        max_phase_seconds=8.0,
        progress_callback=None,
    ):
        """
        Fetch data from a remote test file and stream an upload payload to calculate
        real-time download and upload speeds in Mbps.
        """
        dl_candidates = list(download_urls) if download_urls else list(self.DEFAULT_DOWNLOAD_URLS)
        ul_candidates = list(upload_urls) if upload_urls else list(self.DEFAULT_UPLOAD_URLS)

        download_mbps = 0.0
        upload_mbps = 0.0
        last_dl_error = None

        # 1. Real-time streaming test-file download
        for url in dl_candidates:
            try:
                if progress_callback:
                    progress_callback("Connecting to test file...", 0.0, 0.0)
                headers = {"User-Agent": "SpeedView/1.0", "Cache-Control": "no-cache"}
                with requests.get(url, stream=True, timeout=timeout, headers=headers) as resp:
                    resp.raise_for_status()
                    start = time.perf_counter()
                    last_report = start
                    total_bytes = 0
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        total_bytes += len(chunk)
                        now = time.perf_counter()
                        elapsed = max(1e-6, now - start)
                        live_dl = (total_bytes * 8.0) / (elapsed * 1_000_000.0)
                        if progress_callback and (now - last_report >= 0.12):
                            last_report = now
                            mb_done = total_bytes / (1024 * 1024)
                            progress_callback(f"Downloading test file ({mb_done:.1f} MB)...", live_dl, 0.0)
                        if elapsed >= max_phase_seconds:
                            break
                    if total_bytes <= 0:
                        raise RuntimeError(f"Empty response from {url}")
                    total_elapsed = max(1e-6, time.perf_counter() - start)
                    download_mbps = (total_bytes * 8.0) / (total_elapsed * 1_000_000.0)
                    if progress_callback:
                        progress_callback("Download complete. Testing upload...", download_mbps, 0.0)
                    last_dl_error = None
                    break
            except Exception as exc:
                last_dl_error = exc

        if last_dl_error is not None:
            raise RuntimeError(f"Download test failed: {last_dl_error}")

        # 2. Real-time streaming upload payload
        last_ul_error = None
        for url in ul_candidates:
            try:
                def _on_ul_progress(sent_bytes, live_ul_mbps):
                    if progress_callback:
                        mb_sent = sent_bytes / (1024 * 1024)
                        progress_callback(f"Uploading test payload ({mb_sent:.1f} MB)...", download_mbps, live_ul_mbps)

                reader = _ChunkedUploadReader(
                    total_bytes=upload_size_bytes,
                    chunk_size=chunk_size,
                    on_progress=_on_ul_progress,
                )
                ul_start = time.perf_counter()
                headers = {"Content-Type": "application/octet-stream", "User-Agent": "SpeedView/1.0"}
                resp = requests.post(url, data=reader, headers=headers, timeout=timeout)
                resp.raise_for_status()
                ul_elapsed = max(1e-6, time.perf_counter() - ul_start)
                upload_mbps = (reader.bytes_sent * 8.0) / (ul_elapsed * 1_000_000.0)
                last_ul_error = None
                break
            except Exception as exc:
                last_ul_error = exc

        if last_ul_error is not None and progress_callback:
            progress_callback("Upload endpoint unreachable", download_mbps, 0.0)

        return download_mbps, upload_mbps

    def run_speed_test(self):
        """Start a speed test in a background thread"""
        if self.testing:
            return
        self.testing = True
        thread = threading.Thread(target=self._speed_test_thread, daemon=True)
        thread.start()

    def _emit_test_progress(self, status, download_mbps, upload_mbps):
        if hasattr(self.speed_test_progress, "emit"):
            self.speed_test_progress.emit(status, float(download_mbps), float(upload_mbps))

    def _speed_test_thread(self):
        """Thread to run real-time HTTP test-file network speed test with fallbacks."""
        try:
            download_speed, upload_speed = self.measure_file_speed(
                progress_callback=self._emit_test_progress
            )
            if hasattr(self.speed_test_complete, "emit"):
                self.speed_test_complete.emit(download_speed, upload_speed)
            return
        except Exception as file_exc:
            try:
                self._emit_test_progress("Trying Speedtest server...", 0.0, 0.0)
                import speedtest
                st = speedtest.Speedtest()
                st.get_best_server()
                download_speed = st.download() / 1_000_000
                self._emit_test_progress("Testing upload...", download_speed, 0.0)
                upload_speed = st.upload() / 1_000_000
                if hasattr(self.speed_test_complete, "emit"):
                    self.speed_test_complete.emit(download_speed, upload_speed)
                return
            except Exception as st_exc:
                try:
                    import json
                    result = subprocess.run(
                        ['fast', '--json'],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        download_speed = float(data.get('downloadSpeed', 0))
                        if hasattr(self.speed_test_complete, "emit"):
                            self.speed_test_complete.emit(download_speed, 0.0)
                        return
                    err_msg = f"Speed test failed: {file_exc}; {st_exc}; fast-cli: {result.stderr}"
                except Exception as fallback_e:
                    err_msg = f"Speed test failed: {file_exc}; {st_exc}; {fallback_e}"
                if hasattr(self.speed_test_failed, "emit"):
                    self.speed_test_failed.emit(err_msg)
        finally:
            self.testing = False

    def get_connection_info(self, interface_name=None, use_cache=False):
        """Get real (connection_type, band_or_detail) for the active/selected interface."""
        details = (
            self.get_cached_interface_details(interface_name)
            if use_cache
            else self.get_interface_details(interface_name)
        )
        conn_type = details["connection_type"]
        if conn_type == "Disconnected":
            return "Disconnected", "N/A"
        if conn_type == "Wi-Fi":
            detail_parts = [p for p in (details.get("ssid"), details.get("band")) if p]
            if details.get("link_speed_mbps") and not detail_parts:
                detail_parts.append(f"{details['link_speed_mbps']} Mbps")
            return "Wi-Fi", " • ".join(detail_parts) if detail_parts else (details.get("ipv4") or details.get("interface") or "Wi-Fi")

        # Ethernet / Virtual / Loopback: show link speed and IP instead of fake WiFi/5GHz
        detail_parts = []
        if details.get("link_speed_mbps"):
            detail_parts.append(f"{details['link_speed_mbps']} Mbps")
        if details.get("ipv4"):
            detail_parts.append(details["ipv4"])
        elif details.get("ipv6"):
            detail_parts.append(details["ipv6"])
        elif details.get("interface"):
            detail_parts.append(details["interface"])
        return conn_type, " • ".join(detail_parts) if detail_parts else conn_type