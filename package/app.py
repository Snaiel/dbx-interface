import sys
from json import load
from dropbox import Dropbox
from dropbox.exceptions import AuthError
from PyQt5.QtWidgets import QApplication
from package.ui.main_window import MainWindow
from package.ui.starter_window import StarterWindow

def main():
    app = QApplication(sys.argv)

    try:
        with open('config.json', 'r+') as json_file:
            json_data = load(json_file)
            print(json_data)

            APP_KEY = json_data["APP_KEY"]
            APP_SECRET = json_data["APP_SECRET"]
            ACCESS_TOKEN = json_data["ACCESS_TOKEN"]

            # Create an instance of a Dropbox class, which can make requests to the API.
            dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN)

            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

            window = MainWindow()
            window.show()
    except FileNotFoundError:
        starter_window = StarterWindow()
        starter_window.show()

    

    return app.exec_()