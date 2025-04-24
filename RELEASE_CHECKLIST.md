# SpeedView Release Checklist

## 1. Pre-Release
- [x] Update version number in all relevant files (e.g., config.py, About dialog)
- [x] Ensure README.md is up to date (features, installation, update URL instructions)
- [x] Ensure LICENSE file is present and correct
- [x] Check requirements.txt for all needed dependencies

## 2. Functionality
- [x] Application launches without error on Windows
- [x] Main window displays speed and updates in real time
- [x] System tray integration works (if enabled in settings)
- [ ] Settings dialog opens, saves, and loads all options (including update URL)
- [ ] Update checker works with a real GitHub repo (test with a sample release)
- [x] Floating window launches, updates, and can be closed
- [x] SVG buttons (Test Network, Float, History, Settings) work at all window sizes
- [ ] Network test runs and displays results
- [ ] History window (if implemented) opens and displays past results

## 3. Error Handling
- [ ] App handles no network gracefully (no crash, UI disables test button)
- [ ] Update check fails gracefully if URL is invalid or network is down
- [ ] All dialogs handle invalid input without crashing

## 4. Persistence
- [ ] Settings persist across sessions
- [ ] Window size and position are restored

## 5. Testing
- [x] All unit tests pass (run `python -m unittest discover`)
- [ ] Manual UI test for all dialogs and buttons
- [ ] (Optional) Integration/UI tests pass

## 6. Packaging
- [ ] PyInstaller or other build script creates a working executable
- [ ] Executable runs on a clean Windows VM (no dev tools installed)

## 7. Documentation
- [ ] README includes troubleshooting and FAQ
- [ ] Changelog or release notes are available

## 8. Final
- [ ] Tag release in Git
- [ ] Create GitHub Release with .exe asset and release notes
- [ ] Announce release to users/beta testers
