# SpeedView

SpeedView is a desktop application that provides a clear and real-time visual representation of your network speed.  It uses a speedometer-style interface to display download or upload speeds, giving you instant insight into your network performance.  SpeedView also includes a range of customization options and system tray integration for convenient monitoring.

## Features

* **Real-time Speed Visualization:** A dynamic speedometer display and precise numerical readout provide an at-a-glance view of your current network speed (download or upload).
* **Customizable Settings:**
    * **Maximum Speed:** Configure the maximum speed value displayed on the speedometer to match your network capabilities.
    * **Update Interval:** Adjust the frequency at which the speed is updated to balance responsiveness and system resources.
    * **Start Minimized:** Launch SpeedView in a minimized state for unobtrusive background monitoring.
    * **Minimize to Tray:** Minimize the application to the system tray for easy access and a clutter-free desktop.
    * **Speed Direction:** Choose whether to display download or upload speeds according to your needs.
    * **Network Interface Selection:** Select the specific network interface you want to monitor.
* **System Tray Integration:**
    * SpeedView can be minimized to the system tray for continuous background monitoring.
    * The tray icon displays the current network speed as a tooltip.
    * A context menu provides quick access to the following actions:
        * Show/Hide:  Toggles the visibility of the main application window.
        * Float Mode:  Activates a compact, always-on-top window for a simplified speed display.
        * Settings:  Opens the application's settings dialog for customization.
        * Test Network:  Initiates a network speed test.
        * Exit:  Closes the SpeedView application.
* **Floating Mode:** A compact and always-on-top window that provides a streamlined view of your network speed, ideal for keeping an eye on your connection without taking up much screen space.
* **Integrated Network Testing:** Perform quick speed tests directly within SpeedView using `speedtest-cli` to get detailed download and upload speed measurements.
* **Connection Status and Signal Strength:** SpeedView monitors and displays your current network connection status (Connected or Disconnected) and provides a visual representation of the network signal strength.

## Dependencies

SpeedView relies on the following Python libraries:

* PyQt5
* psutil
* speedtest-cli

## Installation

1.  **Python Installation:** Ensure that you have Python 3.x installed on your system.
2.  **Install Dependencies:** Use pip to install the required libraries:

    ```bash
    pip install PyQt5 psutil speedtest-cli
    ```
3.  **Run SpeedView:** Execute the main script to launch the application:

    ```bash
    python speedview.py
    ```

## Usage

* Upon launching SpeedView, the main window will display your network speed using the speedometer interface.
* **Accessing Settings:** Click the gear icon within the application to open the settings dialog and customize SpeedView's behavior.
* **Float Mode:** Toggle the "Float" button to switch to the compact floating window mode.
* **Performing Speed Tests:** Click the "Test Network" button to initiate a speed test and view your network's download and upload speeds.
* **System Tray Operation:** SpeedView can be minimized to the system tray, allowing you to monitor your network speed discreetly. Use the tray icon's context menu to access SpeedView's functions.

## Code Overview

* `speedview.py`:  This file contains the core application logic for SpeedView, including:
    * `NetworkSpeedMeter` class:  The primary widget responsible for displaying the network speed and handling user interactions.
    * `SettingsDialog` class:  A dialog window that provides users with options to configure SpeedView's settings.
    * `SpeedTestThread` class:  A separate thread used to perform network speed tests without blocking the main application's responsiveness.
*

## Important Notes

* **Platform-Specific Signal Strength:** Currently, signal strength detection is implemented only for Windows using `netsh`.  To ensure cross-platform compatibility, implementations for Linux and macOS are necessary.
* **Error Handling Considerations:** The error handling, particularly for network speed tests, could be enhanced to provide more informative feedback and a more robust user experience.
* **SVG Management:** The application uses regular expressions to modify the SVG content. For more complex SVG manipulations or increased maintainability, consider using a dedicated SVG library.

## Future Enhancements

* Implement signal strength retrieval for Linux and macOS platforms.
* Enhance error handling to provide more user-friendly error messages and recovery options.
* Evaluate and potentially integrate an SVG library for improved SVG manipulation and maintainability.
* Optimize the user interface and update mechanisms for smoother performance and responsiveness.
