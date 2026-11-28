# SpeedView Changelog

All notable releases, features, and improvements for SpeedView.

---

## v1.0.0 — Cross-Platform Auto-Updater, GUI Installer & Live Ping
### Features
- Real-time Ping / Latency badge (`#pingBadge`) next to the main speedometer gauge
- Transparent compact corner Float widget (`136x40`) displaying live signal bars and speed
- High-contrast dark Settings UI with OS `Start on Startup` and one-click `Create Desktop Shortcut`
- Bundled application icon (`speedview.ico` / `speedview.png` / `speedview.icns`) and Inno Setup + PyQt5 GUI Installer/Uninstaller (`Program Files\SpeedView`)
- 3-day rate-limited GitHub Releases background auto-updater with Python subprocess extraction, replacement, and restart

### Changelog
- Switched Windows/Linux builds to `onedir` layout for clean `Program Files\SpeedView` installs and seamless `.zip` updates
- Added Inno Setup 6 script (`installer/windows/speedview.iss`) and PyQt5 GUI Installer/Uninstaller wizard with Desktop & Start Menu shortcuts
- Updated About and Updater widgets to display all released version changelogs & features automatically
- Implemented unified close-to-Float and minimize-to-tray background daemon lifecycle

---

## v0.9.0 — Live File Speed Testing & SQLite Data Usage
### Features
- Real-time HTTP file streaming download & chunked upload speed test (`NetworkController.measure_file_speed`)
- Per-application SQLite Data Usage tracker (`data_usage.db`) with Daily and Monthly breakdowns (`App | Data | Date`)
- System tray dynamic speed badge icon with synced status tooltip and quick actions

### Changelog
- Added `speedtest-cli` and `fast-cli` fallbacks for offline/blocked test endpoints
- Built frameless SVG dialogs for Network Speed Test and Data Usage History
- Fixed live interface detection across Ethernet, Wi-Fi (SSID, band, signal %), Virtual, and Loopback adapters

---

## v0.8.0 — Frameless SVG Speedometer & Floating Widget
### Features
- Translucent frameless SVG main speedometer card (`500x500`) with animated gradient arc
- Switchable Download/Upload gauge scale and units (`Mbps`, `MB/s`, `Kbps`)
- Persistent JSON configuration in OS config directories

### Changelog
- Introduced in-memory SVG template updates (`svg_utils`) eliminating temp disk SVG flicker
- Added keyboard shortcuts (`Ctrl+S`, `Ctrl+T`, `Ctrl+F`, `Ctrl+U`, `Esc`) and desktop threshold alerts
