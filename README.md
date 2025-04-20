# Network Speed Meter

A simple application to monitor network speed using PyQt5.

## Features
- Real-time download and upload speed monitoring
- System tray integration
- User-configurable settings

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zikani/network_speed_meter.git
   cd network_speed_meter
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
This will generate an executable in the `dist`