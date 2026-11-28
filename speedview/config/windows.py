    # Linux / XDG desktop autostart
    try:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if not xdg_config:
            xdg_config = os.path.expanduser("~/.config")
        autostart_dir = os.path.join(xdg_config, "autostart")
        desktop_file = os.path.join(autostart_dir, "speedview.desktop")

        if enable:
            os.makedirs(autostart_dir, exist_ok=True)
            exec_cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
            desktop_content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=SpeedView\n"
                "Comment=Network Speed Meter\n"
                f"Exec={exec_cmd}\n"
                "Terminal=false\n"
                "Categories=Network;Utility;\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            tmp_file = desktop_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(desktop_content)
            os.replace(tmp_file, desktop_file)
        elif os.path.lexists(desktop_file):
            os.remove(desktop_file)

        if enable:
            return os.path.isfile(desktop_file)
        return not os.path.lexists(desktop_file)
    except OSError as e:
        print(f"Error setting Linux autostart: {e}")
        return False
