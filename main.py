import logging
import os
import platform
import sys
import traceback
from PyQt5.QtWidgets import QApplication
from speedview.app import NetworkSpeedMeter
from speedview.ui.update_dialog import UpdateDialog
from speedview.utils.icon_utils import get_app_icon


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
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        logging.info('No display detected on Linux; using QT_QPA_PLATFORM=offscreen')


def check_updates_on_startup(settings=None, force=False):
    from speedview.update.updater import UpdateChecker
    updater = UpdateChecker(settings=settings)
    if updater.check_for_updates(force=force):
        dialog = UpdateDialog(settings=settings, force_check=False)
        dialog.exec_()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        logging.info('Starting SpeedView application')
        _configure_headless_qt()
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