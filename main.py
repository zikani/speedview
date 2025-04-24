import logging
from PyQt5.QtWidgets import QApplication
from speedview.app import NetworkSpeedMeter
from speedview.ui.update_dialog import UpdateDialog
import sys

def check_updates_on_startup():
    from speedview.update.updater import UpdateChecker
    updater = UpdateChecker()
    if updater.check_for_updates():
        dialog = UpdateDialog()
        dialog.exec_()

if __name__ == '__main__':
    import traceback
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        logging.info('Starting SpeedView application')
        app = QApplication(sys.argv)
        # Check for updates on startup
        logging.info('Checking for updates on startup')
        check_updates_on_startup()
        window = NetworkSpeedMeter()
        logging.info('Main window created and shown')
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error('Exception during application startup: %s', e)
        traceback.print_exc()
        import sys
        sys.exit(1)