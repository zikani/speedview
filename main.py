import atexit
import logging
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback

_DISPLAY_PROCS = []


def _is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.05)
        return sock.connect_ex(('127.0.0.1', port)) == 0


def _cleanup_display_procs():
    for proc in reversed(_DISPLAY_PROCS):
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
    deadline = time.monotonic() + 1.0
    for proc in reversed(_DISPLAY_PROCS):
        if proc.poll() is None:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except OSError:
                    pass
    _DISPLAY_PROCS.clear()


def _cleanup_stale_x_lock(display_num: str = '99'):
    lock_file = f'/tmp/.X{display_num}-lock'
    sock_file = f'/tmp/.X11-unix/X{display_num}'
    if os.path.exists(lock_file):
        alive = False
        try:
            with open(lock_file, 'r', encoding='utf-8') as f:
                pid_str = f.read().strip()
            if pid_str.isdigit() and os.path.exists(f'/proc/{pid_str}'):
                alive = True
        except OSError:
            pass
        if not alive:
            for path in (lock_file, sock_file):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _start_virtual_display_server(port: int) -> bool:
    if _is_port_open(port):
        return False
    required_bins = ('Xvfb', 'x11vnc', 'websockify')
    if not all(shutil.which(cmd) for cmd in required_bins) or not os.path.isdir('/usr/share/novnc'):
        return False

    _cleanup_stale_x_lock('99')
    display_env = os.environ.copy()
    display_env['DISPLAY'] = ':99'

    try:
        xvfb_log = open('/tmp/xvfb.log', 'ab')
        xvfb = subprocess.Popen(
            ['Xvfb', ':99', '-screen', '0', '900x700x24'],
            stdout=xvfb_log,
            stderr=subprocess.STDOUT,
        )
        _DISPLAY_PROCS.append(xvfb)

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError('Xvfb exited early')
            if os.path.exists('/tmp/.X11-unix/X99'):
                break
            time.sleep(0.02)
        else:
            raise TimeoutError('Timed out waiting for Xvfb socket')

        if shutil.which('openbox'):
            ob_log = open('/tmp/openbox.log', 'ab')
            openbox = subprocess.Popen(
                ['openbox'],
                env=display_env,
                stdout=ob_log,
                stderr=subprocess.STDOUT,
            )
            _DISPLAY_PROCS.append(openbox)

        vnc_port = 5900
        vnc_log = open('/tmp/x11vnc.log', 'ab')
        x11vnc = subprocess.Popen(
            ['x11vnc', '-display', ':99', '-forever', '-nopw', '-shared', '-rfbport', str(vnc_port)],
            env=display_env,
            stdout=vnc_log,
            stderr=subprocess.STDOUT,
        )
        _DISPLAY_PROCS.append(x11vnc)

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            if x11vnc.poll() is not None:
                raise RuntimeError('x11vnc exited early')
            if _is_port_open(vnc_port):
                break
            time.sleep(0.02)
        else:
            raise TimeoutError('Timed out waiting for x11vnc')

        ws_log = open('/tmp/websockify.log', 'ab')
        websockify = subprocess.Popen(
            ['websockify', '--web=/usr/share/novnc', str(port), f'localhost:{vnc_port}'],
            stdout=ws_log,
            stderr=subprocess.STDOUT,
        )
        _DISPLAY_PROCS.append(websockify)

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            if websockify.poll() is not None:
                raise RuntimeError('websockify exited early')
            if _is_port_open(port):
                break
            time.sleep(0.02)
        else:
            raise TimeoutError('Timed out waiting for websockify')

        atexit.register(_cleanup_display_procs)

        def _handle_sigterm(signum, frame):
            _cleanup_display_procs()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _handle_sigterm)
        os.environ['DISPLAY'] = ':99'
        logging.info('Started virtual display server on DISPLAY=:99 (noVNC on port %s)', port)
        return True
    except Exception as exc:
        logging.warning('Virtual display server failed (%s); falling back to offscreen', exc)
        _cleanup_display_procs()
        return False


def _configure_headless_qt():
    if (
        platform.system() == 'Linux'
        and not os.environ.get('DISPLAY')
        and not os.environ.get('WAYLAND_DISPLAY')
        and not os.environ.get('QT_QPA_PLATFORM')
    ):
        if not os.environ.get('XDG_RUNTIME_DIR'):
            runtime_dir = f'/tmp/runtime-{os.getuid()}'
            os.makedirs(runtime_dir, mode=0o700, exist_ok=True)
            os.environ['XDG_RUNTIME_DIR'] = runtime_dir
        port_str = os.environ.get('PORT', '').strip()
        if port_str.isdigit() and _start_virtual_display_server(int(port_str)):
            return
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        logging.info('No display detected on Linux; using QT_QPA_PLATFORM=offscreen')


def check_updates_on_startup(settings=None, force=False):
    from speedview.update.updater import UpdateChecker
    from speedview.ui.update_dialog import UpdateDialog
    updater = UpdateChecker(settings=settings)
    if updater.check_for_updates(force=force):
        dialog = UpdateDialog(settings=settings, force_check=False)
        dialog.exec_()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        logging.info('Starting SpeedView application')
        _configure_headless_qt()

        from PyQt5.QtWidgets import QApplication
        from speedview.app import NetworkSpeedMeter
        from speedview.utils.icon_utils import get_app_icon

        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setWindowIcon(get_app_icon())

        window = NetworkSpeedMeter()
        logging.info('Background auto-updater scheduled on a 3-day check interval')

        # Honor start_minimized and is_floating before showing the main window
        if not window.settings.start_minimized and not window.settings.is_floating:
            window.show()
            logging.info('Main window created and shown')
        else:
            logging.info('Main window started minimized or in floating mode')

        sys.exit(app.exec_())
    except Exception as e:
        logging.error('Exception during application startup: %s', e)
        traceback.print_exc()
        sys.exit(1)