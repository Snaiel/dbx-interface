import sys
import json
import package.utils as utils
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from package.ui.main_window import MainWindow
from package.ui.starter_window import StarterWindow
from package.ui.delete_nonexistent import DeleteNonExistent

def run(setup: bool = False) -> int:
    app = QApplication(sys.argv)
    if not Path(Path(__file__).parents[1], 'config.json').is_file() or setup:
        if not run_setup():
            return 0
        
    dbx = utils.create_dbx()
    if not utils.validate_dbx(dbx):
        print("ERROR: The provided Dropbox info is invalid")
        print_error_help()
        return 0

    with open(Path(Path(__file__).parents[1], 'config.json')) as json_file:
        json_data = json.load(json_file)

        try:
            if json_data['DROPBOX_LOCATION'] == "":
                print("ERROR: You must provide the location of your local Dropbox folder.")
                print_error_help()
                return 0
        except KeyError:
            print("ERROR: You must provide the location of your local Dropbox folder.")
            print_error_help()
            return 0
        
    paths_to_delete = utils.clean_synced_paths(json_data['DROPBOX_LOCATION'])
    print("Starting application")
    if paths_to_delete:
        delete_nonexistent = DeleteNonExistent(dbx, paths_to_delete)
        delete_nonexistent.exec_()

    window = MainWindow(dbx, json_data['DROPBOX_LOCATION'])
    window.show()

    return app.exec_()

def run_setup() -> bool:
    starter_window = StarterWindow()
    starter_window.setAttribute(Qt.WA_DeleteOnClose)
    starter_window.exec_()
    return starter_window.setup_complete

def print_error_help():
    print("Run setup again with `python3 main.py setup`")