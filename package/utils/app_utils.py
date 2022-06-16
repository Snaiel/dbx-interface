"""
This module accesses Dropbox
Takes care of auth and gets the files & folders
"""

from pathlib import Path
import requests
import json
from dropbox import Dropbox
from dropbox.exceptions import AuthError

def create_dbx() -> Dropbox:
    with open(Path(Path(__file__).parents[2], 'config.json'), 'r+') as json_file:
        json_data = json.load(json_file)
        # print(json_data)

        APP_KEY = json_data["APP_KEY"]
        APP_SECRET = json_data["APP_SECRET"]
        ACCESS_TOKEN = json_data["ACCESS_TOKEN"]
        REFRESH_TOKEN = json_data["REFRESH_TOKEN"]

        return Dropbox(app_key=APP_KEY, app_secret=APP_SECRET, oauth2_access_token=ACCESS_TOKEN, oauth2_refresh_token=REFRESH_TOKEN)

def validate_dbx(dbx: Dropbox) -> bool:
    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
        return True
    except AuthError:
        return False

def create_config(code, app_key, app_secret, dropbox_location):
    data = {
            'code': code,
            'grant_type': 'authorization_code',
        }

    r = requests.post('https://api.dropbox.com/oauth2/token', data=data, auth=(app_key, app_secret))
    r_data = r.json()

    config_data = {
        'DROPBOX_LOCATION': dropbox_location,
        'APP_KEY': app_key,
        'APP_SECRET': app_secret,
        'ACCESS_TOKEN': r_data["access_token"],
        'REFRESH_TOKEN': r_data["refresh_token"]
    }

    with open("config.json", "w") as json_file:
        json.dump(config_data, json_file, indent=4)