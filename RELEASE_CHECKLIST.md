# SpeedView Release Checklist

## 1. Pre-Release
- [x] Update version number in `speedview/config/config.py` (`APP_VERSION`) and About dialog
- [x] Ensure `README.md` is up to date (cross-platform installation, features, Data Usage, shortcuts, update URL)
- [x] Ensure `LICENSE` file is present and correct
- [x] Check `requirements.txt` includes cross-platform environment markers (`pywin32`, `winshell` gated to `win32`)

## 2. Functionality
- [x] Application launches without error on Linux (`Xvfb` / desktop) and guards Windows-only modules (`winreg`, `win32*`, `winshell`)
- [x] Main frameless SVG speedometer displays real-time speed and updates via `SpeedController`
- [x] Real network interface detection reports Ethernet / Wi-Fi / Virtual / Loopback, IPv4/IPv6, link speed, and SSID/band
- [x] System tray integration works (`Show`, `Float Mode`, `Data Usage`, `Settings`, `Test Network`, `Exit`) with synced tooltip
- [x] Settings dialog opens, loads via `findData()`/`itemData()`, validates, saves, restores defaults, and syncs live UI
- [x] Floating window launches, updates in memory via SVG, and syncs close/expand state with `MainWindow`
- [x] SVG buttons (`FLOAT`, `TEST NETWORK`, `USAGE`, Settings, Minimize, Close) work cleanly
- [x] Data Usage SVG window opens and displays `App | Data | Date` for Daily and Monthly views backed by SQLite
- [ ] Update checker verified against a published GitHub release asset on Windows & Linux

## 3. Error Handling
- [x] App handles disconnected network / failed speed test gracefully without UI freezes
- [x] Update check and non-Windows release fallback (`webbrowser.open`) handle errors gracefully
- [x] Dialogs validate input without crashing

## 4. Persistence
- [x] Settings persist across sessions in `network_speed_meter.conf`
- [x] Window size, position, `start_minimized`, and `is_floating` are restored on launch
- [x] Daily and monthly traffic data persists in `data_usage.db`

## 5. Testing & CI
- [x] Bytecode check (`python -m compileall main.py speedview tests`) passes cleanly
- [x] All unit tests pass (`python -m unittest discover -s tests -v`)
- [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`) configured for Ubuntu and Windows

## 6. Packaging & Release
- [ ] PyInstaller build verified for target OS binaries
- [ ] Tag release in Git (`vX.Y.Z`) and publish GitHub Release with changelog notes
