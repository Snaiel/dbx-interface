import sys
import package.dbx_utils as dbx_utils
import os.path
from pathlib import Path
from json import load
from dropbox import Dropbox
from dropbox.exceptions import AuthError
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QEventLoop
from package.ui.main_window import MainWindow
from package.ui.starter_window import StarterWindow

def run():
    app = QApplication(sys.argv)
    if not Path(Path(__file__).parents[1], 'config.json').is_file():
        starter_window = StarterWindow()
        starter_window.setAttribute(Qt.WA_DeleteOnClose)
        starter_window.exec_()
        # print(starter_window.setup_complete)
        if starter_window.setup_complete:
            dbx = dbx_utils.create_dbx()
            window = MainWindow(dbx)
            window.show()
        else:
            return 0
    else:
        dbx = dbx_utils.create_dbx()
        window = MainWindow(dbx)
        window.show()

    return app.exec_()