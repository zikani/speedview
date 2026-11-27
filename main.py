import logging
import sys
import traceback
from PyQt5.QtWidgets import QApplication
from speedview.app import NetworkSpeedMeter
from speedview.ui.update_dialog import UpdateDialog


def check_updates_on_startup(settings=None):
    from speedview.update.updater import UpdateChecker
    updater = UpdateChecker(settings=settings)
    if updater.check_for_updates():
        dialog = UpdateDialog(settings=settings)
        dialog.exec_()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        logging.info('Starting SpeedView application')
        app = QApplication(sys.argv)

        window = NetworkSpeedMeter()
        logging.info('Checking for updates on startup')
        check_updates_on_startup(settings=window.settings)

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