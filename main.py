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
    app = QApplication(sys.argv)
    
    # Check for updates on startup
    check_updates_on_startup()
    
    window = NetworkSpeedMeter()
    window.show()
    sys.exit(app.exec_())