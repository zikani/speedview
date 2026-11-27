# SpeedView

A cross-platform desktop network speed monitor built with Python, PyQt5, and SVG.

## Features
- **Frameless SVG Speedometer Gauge**: Translucent rounded card displaying real-time download or upload speed, dynamic arc & dial scaling, and connection status (`Connected`, `Disconnected`, `Checking...`).
- **Real Network Interface Detection**: Automatically detects active Ethernet, Wi-Fi (SSID, frequency band `2.4GHz`/`5GHz`/`6GHz`, signal strength), Virtual, or Loopback interfaces along with link speed and IPv4/IPv6 addresses across Linux, Windows, and macOS.
- **Floating Compact Widget**: Always-on-top mini SVG speed pill with drag-to-move, signal bars, interface summary, and quick expand/close controls.
- **SVG Network Speed Test**: Integrated speed test dialog powered by `speedtest-cli` (with `fast-cli` fallback) displaying live status, download/upload Mbps, and progress bars.
- **Data Usage Window (`App | Data | Date`)**: SQLite-backed daily and monthly traffic tracking (`data_usage.db`) attributed across active socket processes, with an SVG viewer featuring `DAILY` / `MONTHLY` tabs and `RESET`.
- **System Tray Integration**: Dynamic speed badge icon, synced tooltip (download/upload speed, connection state, active interface), high-speed alert notifications, and quick actions (`Show`, `Float Mode`, `Data Usage`, `Settings`, `Test Network`, `Exit`).
- **Configurable Settings**: Select specific interface or enable `Auto-select best interface`, customize max gauge limits, speed unit (`Mbps`, `MB/s`, `Kbps`), update interval, tray behavior, notifications, and update URL.

## Requirements
- **Python**: 3.8 or higher (tested on Python 3.11)
- **Operating Systems**: Windows, Linux, or macOS
- **Dependencies** (`requirements.txt`): `PyQt5`, `psutil`, `speedtest-cli`, `requests`, `packaging`, and on Windows `pywin32`, `winshell`

On Linux (Debian/Ubuntu), if installing PyQt5 via system packages or running headless tests:
```bash
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtsvg python3-psutil python3-requests python3-packaging speedtest-cli
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zikani/speedview.git
   cd speedview
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # Linux/macOS:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Usage & Shortcuts
- **Main SVG Controls**: Click `FLOAT`, `TEST NETWORK`, `USAGE`, the top-right settings gear, or minimize/close controls; drag anywhere on the card background to reposition.
- **System Tray**: Right-click for `Show`, `Float Mode`, `Data Usage`, `Settings`, `Test Network`, and `Exit`; double-click to show/hide; middle-click to run a speed test.
- **Keyboard Shortcuts**:
  - `Ctrl+S`: Open Settings
  - `Ctrl+T`: Run Network Speed Test
  - `Ctrl+F`: Toggle Floating Mode
  - `Ctrl+U` / `Ctrl+H`: Open Data Usage window
  - `Esc`: Close dialog / hide when in floating mode

## Configuration & Storage
Settings are stored as JSON in the OS user config directory (`%APPDATA%\NetworkSpeedMeter\network_speed_meter.conf` on Windows, `$XDG_CONFIG_HOME/NetworkSpeedMeter/network_speed_meter.conf` or `~/.config/NetworkSpeedMeter/network_speed_meter.conf` on Linux/macOS).

Default configuration values (`speedview/config/config.py`):
- `max_speed`: `100` Mbps download scale
- `max_upload`: `50` Mbps upload scale
- `update_interval`: `1.0` seconds
- `speed_unit`: `"Mbps"` (`Mbps`, `MB/s`, `Kbps`)
- `minimize_to_tray`: `true`
- `close_to_tray`: `true`
- `enable_notifications`: `true` (`notification_threshold`: `50` Mbps)

Per-app traffic records are stored in `data_usage.db` inside the same `NetworkSpeedMeter` config directory.

## Testing & CI
Run the full unit test suite (use `xvfb-run -a` on headless Linux):
```bash
python -m compileall main.py speedview tests
python -m unittest discover -s tests -v
```

Automated CI runs via `.github/workflows/ci.yml` on `ubuntu-latest` and `windows-latest` for every push and pull request.

## Troubleshooting
1. **Linux headless / Wayland Qt errors**: Ensure `PyQt5` SVG libraries and X11/xcb runtime dependencies (`libxcb-xinerama0`, `libxkbcommon-x11-0`, `libgl1`) are installed.
2. **Speed test fails behind proxy/offline**: `NetworkController` tries `speedtest-cli` and falls back to `fast-cli` (`fast --json`), showing the failure reason directly in the SVG test dialog.
3. **Zero per-app traffic in Data Usage**: On Linux/macOS, inspecting other users' socket PIDs may require elevated permissions; traffic for the current user's processes is attributed automatically, with unmatched bytes grouped under `System / Other`.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.