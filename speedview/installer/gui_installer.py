import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from speedview.config.config import APP_VERSION
from speedview.config.windows import (
    INSTALL_DIR,
    apply_startup_setting,
    create_desktop_shortcut,
    create_start_menu_shortcut,
    create_uninstall_reg_key,
    remove_desktop_shortcut,
    remove_start_menu_shortcut,
    remove_uninstall_reg_key,
)
from speedview.utils.icon_utils import get_app_icon


INSTALLER_QSS = """
QDialog {
    background-color: #0B1220;
    color: #F2F6FF;
    font-family: Inter, 'Segoe UI', Roboto, Arial, sans-serif;
    font-size: 13px;
}
QFrame#installerHeader, QFrame#installerCard {
    background-color: #111B2E;
    border: 1px solid #1E2E4A;
    border-radius: 12px;
}
QLabel#titleLabel {
    color: #F2F6FF;
    font-size: 18px;
    font-weight: 700;
}
QLabel#subtitleLabel {
    color: #22D3EE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#sectionHeading {
    color: #22D3EE;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QLabel {
    color: #CBD5F5;
    background: transparent;
}
QLineEdit {
    background-color: #080E1A;
    color: #F2F6FF;
    border: 1px solid #243656;
    border-radius: 8px;
    padding: 7px 10px;
}
QLineEdit:focus {
    border-color: #22D3EE;
}
QCheckBox {
    color: #E2ECFF;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1.5px solid #334A70;
    background-color: #080E1A;
}
QCheckBox::indicator:checked {
    background-color: #22D3EE;
    border-color: #22D3EE;
}
QProgressBar {
    background-color: #080E1A;
    border: 1px solid #243656;
    border-radius: 6px;
    text-align: center;
    color: #F2F6FF;
    min-height: 18px;
}
QProgressBar::chunk {
    background-color: #22D3EE;
    border-radius: 5px;
}
QPushButton {
    background-color: #16233B;
    color: #E2ECFF;
    border: 1px solid #283C61;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #1E2F4E;
    border-color: #22D3EE;
    color: #FFFFFF;
}
QPushButton#primaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    font-weight: 700;
}
QPushButton#primaryBtn:hover {
    background-color: #3B82F6;
}
QPushButton#dangerBtn {
    background-color: #7F1D1D;
    color: #FEE2E2;
    border: 1px solid #EF4444;
    font-weight: 700;
}
QPushButton#dangerBtn:hover {
    background-color: #991B1B;
}
"""


class InstallerCore:
    """Cross-platform SpeedView installer/uninstaller engine (Program Files / onedir layout)."""

    def __init__(self, payload_dir=None):
        self.payload_dir = os.path.abspath(payload_dir) if payload_dir else self.resolve_payload_dir()

    @staticmethod
    def resolve_payload_dir():
        """Locate bundled SpeedView onedir payload or local dist/SpeedView directory."""
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = os.path.join(meipass, "payload")
            if os.path.isdir(bundled) and os.listdir(bundled):
                return bundled

        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            sibling_payload = os.path.join(exe_dir, "payload")
            if os.path.isdir(sibling_payload) and os.listdir(sibling_payload):
                return sibling_payload
            return exe_dir

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        dist_onedir = os.path.join(project_root, "dist", "SpeedView")
        if os.path.isdir(dist_onedir) and os.listdir(dist_onedir):
            return dist_onedir
        return project_root

    @staticmethod
    def find_installed_binary(install_dir):
        """Return installed launcher binary path if present inside install_dir."""
        for candidate in ("SpeedView.exe", "SpeedView", "SpeedView-linux-x64", "main.py"):
            full = os.path.join(install_dir, candidate)
            if os.path.isfile(full):
                return full
        return None

    @staticmethod
    def is_installed(install_dir):
        return bool(install_dir and os.path.isdir(install_dir) and InstallerCore.find_installed_binary(install_dir))

    @staticmethod
    def _stop_running_app(install_dir=None):
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "SpeedView.exe"],
                    capture_output=True,
                    check=False,
                )
            elif system in ("Linux", "Darwin"):
                if install_dir:
                    subprocess.run(
                        ["pkill", "-f", os.path.abspath(install_dir)],
                        capture_output=True,
                        check=False,
                    )
        except Exception:
            pass

    @staticmethod
    def _copy_source_tree(src_root, dest_dir):
        """Copy clean source runtime files when installing without a prebuilt dist/SpeedView payload."""
        os.makedirs(dest_dir, exist_ok=True)
        for rel in ("main.py", "CHANGELOG.md", "LICENSE", "README.md", "requirements.txt"):
            src = os.path.join(src_root, rel)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(dest_dir, rel))
        pkg_src = os.path.join(src_root, "speedview")
        if os.path.isdir(pkg_src):
            shutil.copytree(
                pkg_src,
                os.path.join(dest_dir, "speedview"),
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )

    @staticmethod
    def _copy_payload(payload_dir, dest_dir, progress_callback=None):
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.isfile(os.path.join(payload_dir, "main.py")) and not (
            os.path.isfile(os.path.join(payload_dir, "SpeedView.exe"))
            or os.path.isfile(os.path.join(payload_dir, "SpeedView"))
        ):
            if progress_callback:
                progress_callback(45, "Copying SpeedView application package...")
            InstallerCore._copy_source_tree(payload_dir, dest_dir)
            if progress_callback:
                progress_callback(75, "Application files installed.")
            return

        # Unwrap single top-level SpeedView folder inside payload if present
        entries = os.listdir(payload_dir)
        effective_src = payload_dir
        if len(entries) == 1 and os.path.isdir(os.path.join(payload_dir, entries[0])):
            inner = os.path.join(payload_dir, entries[0])
            if os.path.isfile(os.path.join(inner, "SpeedView.exe")) or os.path.isfile(os.path.join(inner, "SpeedView")):
                effective_src = inner

        all_items = []
        for root, dirs, files in os.walk(effective_src):
            for f in files:
                src_file = os.path.join(root, f)
                rel = os.path.relpath(src_file, effective_src)
                all_items.append((src_file, os.path.join(dest_dir, rel)))

        total = max(1, len(all_items))
        for idx, (src_file, dst_file) in enumerate(all_items, start=1):
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            if platform.system() != "Windows" and os.path.basename(dst_file) in ("SpeedView", "SpeedView-linux-x64"):
                os.chmod(dst_file, os.stat(dst_file).st_mode | stat.S_IXUSR)
            if progress_callback and (idx % 10 == 0 or idx == total):
                pct = 20 + int((idx / total) * 55)
                progress_callback(pct, f"Extracting files ({idx}/{total})...")

    def install(
        self,
        install_dir=None,
        desktop_shortcut=True,
        start_menu_shortcut=True,
        start_on_startup=False,
        stop_running=True,
        progress_callback=None,
    ):
        """Install or upgrade SpeedView into install_dir (default Program Files\\SpeedView)."""
        target_dir = os.path.abspath(install_dir or INSTALL_DIR)
        if progress_callback:
            progress_callback(5, f"Preparing installation in {target_dir}...")

        if stop_running:
            self._stop_running_app(target_dir)

        if os.path.abspath(self.payload_dir) != target_dir:
            self._copy_payload(self.payload_dir, target_dir, progress_callback=progress_callback)

        # Copy self into install_dir as uninstaller when frozen as SpeedView-Setup
        uninstaller_path = None
        if getattr(sys, "frozen", False) and os.path.isfile(sys.executable):
            setup_name = "SpeedView-Setup.exe" if platform.system() == "Windows" else "SpeedView-Setup"
            dest_setup = os.path.join(target_dir, setup_name)
            try:
                if os.path.abspath(sys.executable) != os.path.abspath(dest_setup):
                    shutil.copy2(sys.executable, dest_setup)
                uninstaller_path = dest_setup
            except OSError:
                pass
        else:
            # Create source-based uninstall launcher reference
            installer_script = os.path.abspath(__file__)
            uninstaller_path = os.path.join(target_dir, "installer.py")
            root_installer = os.path.abspath(os.path.join(os.path.dirname(installer_script), "..", "..", "installer.py"))
            if os.path.isfile(root_installer) and not os.path.exists(uninstaller_path):
                try:
                    shutil.copy2(root_installer, uninstaller_path)
                except OSError:
                    pass

        launched_target = self.find_installed_binary(target_dir)
        ico_candidate = os.path.join(target_dir, "_internal", "speedview", "ui", "resources", "speedview.ico")
        if not os.path.exists(ico_candidate):
            ico_candidate = os.path.join(target_dir, "speedview", "ui", "resources", "speedview.ico")
        png_candidate = os.path.join(target_dir, "_internal", "speedview", "ui", "resources", "speedview.png")
        if not os.path.exists(png_candidate):
            png_candidate = os.path.join(target_dir, "speedview", "ui", "resources", "speedview.png")
        chosen_icon = ico_candidate if platform.system() == "Windows" and os.path.exists(ico_candidate) else png_candidate
        if not os.path.exists(chosen_icon):
            chosen_icon = None

        shortcut_target = launched_target
        if launched_target and launched_target.endswith(".py"):
            shortcut_target = None  # let shortcut helper invoke python + main.py cleanly if run from source

        if progress_callback:
            progress_callback(82, "Creating shortcuts and system registration...")

        if desktop_shortcut:
            create_desktop_shortcut(target_path=shortcut_target, icon_path=chosen_icon)

        if start_menu_shortcut:
            create_start_menu_shortcut(
                target_path=shortcut_target,
                icon_path=chosen_icon,
                uninstaller_path=uninstaller_path if (uninstaller_path and platform.system() == "Windows") else None,
            )

        if start_on_startup:
            apply_startup_setting(True)

        if platform.system() == "Windows":
            uninstall_cmd = f'"{uninstaller_path}" --uninstall --dir "{target_dir}"' if uninstaller_path else None
            create_uninstall_reg_key(
                install_dir=target_dir,
                uninstall_cmd=uninstall_cmd,
                icon_path=launched_target,
                version_str=APP_VERSION,
            )

        if progress_callback:
            progress_callback(100, "SpeedView installation complete!")

        return {
            "install_dir": target_dir,
            "executable": launched_target,
            "uninstaller": uninstaller_path,
        }

    def uninstall(self, install_dir=None, stop_running=True, allow_deferred_cleanup=True, progress_callback=None):
        """Remove SpeedView application folder, shortcuts, autostart, and uninstall registry entry."""
        target_dir = os.path.abspath(install_dir or INSTALL_DIR)
        if progress_callback:
            progress_callback(10, "Stopping SpeedView background process...")

        if stop_running:
            self._stop_running_app(target_dir)

        if progress_callback:
            progress_callback(35, "Removing Desktop & Start Menu shortcuts...")
        remove_desktop_shortcut()
        remove_start_menu_shortcut()
        apply_startup_setting(False)
        remove_uninstall_reg_key()

        if progress_callback:
            progress_callback(70, f"Removing files from {target_dir}...")

        running_inside_target = (
            getattr(sys, "frozen", False)
            and os.path.commonpath([os.path.abspath(sys.executable), target_dir]) == target_dir
        )

        if os.path.isdir(target_dir):
            if running_inside_target and allow_deferred_cleanup:
                self._schedule_self_delete(target_dir)
            else:
                shutil.rmtree(target_dir, ignore_errors=True)

        if progress_callback:
            progress_callback(100, "SpeedView uninstalled cleanly.")
        return True

    @staticmethod
    def _schedule_self_delete(target_dir):
        """Spawn a small detached script to remove install_dir once the uninstaller exits."""
        pid = os.getpid()
        if platform.system() == "Windows":
            fd, bat_path = tempfile.mkstemp(prefix="speedview_uninstall_", suffix=".bat")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(
                    "@echo off\r\n"
                    f"set RETRIES=0\r\n"
                    ":waitloop\r\n"
                    f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul\r\n'
                    "if %ERRORLEVEL%==0 (\r\n"
                    "  set /A RETRIES+=1\r\n"
                    "  if %RETRIES% LSS 20 (\r\n"
                    "    timeout /t 1 /nobreak > nul\r\n"
                    "    goto waitloop\r\n"
                    "  )\r\n"
                    ")\r\n"
                    f'if exist "{target_dir}" rmdir /S /Q "{target_dir}"\r\n'
                    '(goto) 2>nul & del "%~f0"\r\n'
                )
            flags = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
            subprocess.Popen(["cmd", "/c", bat_path], creationflags=flags, close_fds=True)
        else:
            fd, sh_path = tempfile.mkstemp(prefix="speedview_uninstall_", suffix=".sh")
            q_dir = "'" + target_dir.replace("'", "'\"'\"'") + "'"
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(
                    "#!/bin/sh\n"
                    f"while kill -0 {pid} 2>/dev/null; do sleep 0.2; done\n"
                    f"rm -rf {q_dir}\n"
                    'rm -f "$0"\n'
                )
            os.chmod(sh_path, 0o755)
            subprocess.Popen(
                ["/bin/sh", sh_path],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )


class InstallerWorker(QThread):
    progress = pyqtSignal(int, str)
    completed = pyqtSignal(bool, str, str)

    def __init__(self, core, mode, install_dir, desktop_shortcut, start_menu_shortcut, start_on_startup):
        super().__init__()
        self.core = core
        self.mode = mode
        self.install_dir = install_dir
        self.desktop_shortcut = desktop_shortcut
        self.start_menu_shortcut = start_menu_shortcut
        self.start_on_startup = start_on_startup

    def run(self):
        try:
            if self.mode == "uninstall":
                self.core.uninstall(
                    install_dir=self.install_dir,
                    progress_callback=lambda pct, msg: self.progress.emit(pct, msg),
                )
                self.completed.emit(True, "SpeedView has been uninstalled.", "")
            else:
                result = self.core.install(
                    install_dir=self.install_dir,
                    desktop_shortcut=self.desktop_shortcut,
                    start_menu_shortcut=self.start_menu_shortcut,
                    start_on_startup=self.start_on_startup,
                    progress_callback=lambda pct, msg: self.progress.emit(pct, msg),
                )
                exe = result.get("executable") or ""
                self.completed.emit(True, f"SpeedView v{APP_VERSION} installed successfully.", exe)
        except Exception as exc:
            self.completed.emit(False, str(exc), "")


class InstallerWindow(QDialog):
    """GUI Installer / Uninstaller Wizard for extracting SpeedView to Program Files cleanly."""

    def __init__(self, parent=None, default_dir=None, uninstall_mode=False):
        super().__init__(parent)
        self.core = InstallerCore()
        self.default_dir = default_dir or INSTALL_DIR
        self.uninstall_mode = uninstall_mode
        self.worker = None
        self.installed_exe = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"SpeedView Setup v{APP_VERSION}")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(520, 430)
        self.resize(540, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(INSTALLER_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setObjectName("installerHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 12, 14, 12)
        h_layout.setSpacing(12)

        icon_lbl = QLabel(self)
        icon = get_app_icon()
        if not icon.isNull():
            icon_lbl.setPixmap(icon.pixmap(48, 48))
        icon_lbl.setFixedSize(48, 48)
        h_layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        self.title_label = QLabel("SpeedView Setup Wizard")
        self.title_label.setObjectName("titleLabel")
        self.subtitle_label = QLabel(
            f"v{APP_VERSION}  •  Install, Upgrade, or Uninstall in Program Files"
        )
        self.subtitle_label.setObjectName("subtitleLabel")
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)
        h_layout.addLayout(title_col, 1)
        layout.addWidget(header)

        card = QFrame(self)
        card.setObjectName("installerCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 14, 14, 14)
        c_layout.setSpacing(10)

        path_heading = QLabel("DESTINATION FOLDER")
        path_heading.setObjectName("sectionHeading")
        c_layout.addWidget(path_heading)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit(self.default_dir)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.choose_directory)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(self.browse_btn)
        c_layout.addLayout(path_row)

        opts_heading = QLabel("INSTALLATION OPTIONS")
        opts_heading.setObjectName("sectionHeading")
        c_layout.addWidget(opts_heading)

        self.desktop_cb = QCheckBox("Create Desktop shortcut icon")
        self.desktop_cb.setChecked(True)
        c_layout.addWidget(self.desktop_cb)

        self.startmenu_cb = QCheckBox("Create Start Menu / Applications shortcut")
        self.startmenu_cb.setChecked(True)
        c_layout.addWidget(self.startmenu_cb)

        self.autostart_cb = QCheckBox("Start SpeedView automatically on system startup")
        self.autostart_cb.setChecked(False)
        c_layout.addWidget(self.autostart_cb)

        self.launch_cb = QCheckBox("Launch SpeedView after setup completes")
        self.launch_cb.setChecked(True)
        c_layout.addWidget(self.launch_cb)

        layout.addWidget(card)

        self.status_label = QLabel(
            "Ready to uninstall SpeedView."
            if self.uninstall_mode
            else "Ready to extract and install SpeedView."
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setObjectName("dangerBtn")
        self.uninstall_btn.clicked.connect(self.start_uninstall)
        btn_row.addWidget(self.uninstall_btn)

        btn_row.addStretch(1)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.close_btn)

        self.install_btn = QPushButton("Install / Update")
        self.install_btn.setObjectName("primaryBtn")
        self.install_btn.clicked.connect(self.start_install)
        btn_row.addWidget(self.install_btn)

        layout.addLayout(btn_row)

        if self.uninstall_mode:
            self.title_label.setText("Uninstall SpeedView")
            self.desktop_cb.setEnabled(False)
            self.startmenu_cb.setEnabled(False)
            self.autostart_cb.setEnabled(False)
            self.launch_cb.setEnabled(False)
            self.install_btn.hide()

    def choose_directory(self):
        chosen = QFileDialog.getExistingDirectory(
            self, "Select SpeedView Install Folder", self.path_input.text().strip() or self.default_dir
        )
        if chosen:
            self.path_input.setText(chosen)

    def _set_busy(self, busy):
        self.install_btn.setEnabled(not busy)
        self.uninstall_btn.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)
        self.path_input.setEnabled(not busy)

    def start_install(self):
        target_dir = self.path_input.text().strip() or self.default_dir
        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.worker = InstallerWorker(
            self.core,
            mode="install",
            install_dir=target_dir,
            desktop_shortcut=self.desktop_cb.isChecked(),
            start_menu_shortcut=self.startmenu_cb.isChecked(),
            start_on_startup=self.autostart_cb.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_finished_install)
        self.worker.start()

    def start_uninstall(self):
        target_dir = self.path_input.text().strip() or self.default_dir
        reply = QMessageBox.question(
            self,
            "Uninstall SpeedView",
            f"Remove SpeedView and shortcuts from:\n{target_dir}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.worker = InstallerWorker(
            self.core,
            mode="uninstall",
            install_dir=target_dir,
            desktop_shortcut=False,
            start_menu_shortcut=False,
            start_on_startup=False,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_finished_uninstall)
        self.worker.start()

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(max(0, min(100, int(pct))))
        self.status_label.setText(msg)

    def _on_finished_install(self, ok, message, exe_path):
        self._set_busy(False)
        if ok:
            self.installed_exe = exe_path
            self.status_label.setText(message)
            QMessageBox.information(self, "Installation Complete", message)
            if self.launch_cb.isChecked() and exe_path and os.path.exists(exe_path):
                if exe_path.endswith(".py"):
                    subprocess.Popen([sys.executable, exe_path], close_fds=True)
                else:
                    subprocess.Popen([exe_path], close_fds=True)
            self.accept()
        else:
            self.status_label.setText(f"Installation error: {message}")
            QMessageBox.critical(self, "Installation Error", message)

    def _on_finished_uninstall(self, ok, message, _exe_path):
        self._set_busy(False)
        if ok:
            self.status_label.setText(message)
            QMessageBox.information(self, "Uninstall Complete", message)
            self.accept()
        else:
            self.status_label.setText(f"Uninstall error: {message}")
            QMessageBox.critical(self, "Uninstall Error", message)


def main_installer(argv=None):
    parser = argparse.ArgumentParser(description="SpeedView GUI Installer & Uninstaller")
    parser.add_argument("--uninstall", action="store_true", help="Run in uninstall mode")
    parser.add_argument("--dir", dest="install_dir", default=INSTALL_DIR, help="Target install directory")
    parser.add_argument("--silent", action="store_true", help="Run install/uninstall silently without GUI")
    args = parser.parse_args(argv)

    if args.silent:
        core = InstallerCore()
        if args.uninstall:
            core.uninstall(install_dir=args.install_dir)
        else:
            core.install(install_dir=args.install_dir)
        return 0

    app = QApplication.instance() or QApplication(sys.argv)
    app.setWindowIcon(get_app_icon())
    win = InstallerWindow(default_dir=args.install_dir, uninstall_mode=args.uninstall)
    win.show()
    return app.exec_()
