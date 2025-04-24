# SpeedView

A simple application to monitor network speed using PyQt5.

## Features
- Real-time download and upload speed monitoring
- System tray integration
- User-configurable settings
- Floating window mode
- Network speed testing
- Historical data tracking

## Requirements
- Python 3.7 or higher
- Windows operating system

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zikani/speedview.git
   cd speedview
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Packaging the Application
To create a standalone executable for Windows, use PyInstaller:
```bash
python build.py
```
This will generate an executable in the `dist` directory.

## Troubleshooting

### Common Issues
1. If the application fails to start, ensure all dependencies are installed correctly
2. For system tray issues, verify that system tray integration is enabled in Windows
3. If network testing fails, check your internet connection

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Configuration
Settings can be modified in `config.json`:
```json
{
    "update_interval": 1000,
    "start_minimized": false,
    "show_notifications": true,
    "theme": "light"
}
```

## Usage
- Right-click the system tray icon to access settings
- Double-click to show/hide the main window
- Click and drag the floating window to reposition
- Press `Ctrl+Q` to quit
- Use `Ctrl+H` to view history

## Development Setup
1. Set up a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

## Screenshots
![Main Window](screenshots/main.png)
![Floating Mode](screenshots/floating.png)

## System Requirements
- Windows 10 or later
- Minimum 2GB RAM
- 100MB free disk space
- Active internet connection

## Version History
- v1.0.0: Initial release
- v1.1.0: Added floating mode
- v1.2.0: Historical data tracking

## Support
For bug reports and feature requests, please use the [issue tracker](https://github.com/zikani/speedview/issues).