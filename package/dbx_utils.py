"""
This module accesses Dropbox
Takes care of auth and gets the files & folders
"""

import sys
from pathlib import Path
import requests
import json
from dropbox import Dropbox
from dropbox.exceptions import AuthError
from dropbox.files import FileMetadata

def create_dbx() -> Dropbox:
    with open(Path(Path(__file__).parents[1], 'config.json'), 'r+') as json_file:
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

def get_list_of_paths(dbx: Dropbox, root: str) -> list:

    file_list = []

    files = dbx.files_list_folder(root)

    def process_entries(entries):
        for entry in entries:
            file_list.append(entry)

    process_entries(files.entries)

    while files.has_more:
        files = dbx.files_list_folder_continue(files.cursor)

        process_entries(files.entries)

    file_list.sort(key= lambda x: x.path_lower)

    file_list = [{'path':i.path_display, 'is_file':isinstance(i, FileMetadata)} for i in file_list]

    return file_list

def print_list_of_paths(dbx: Dropbox, directory: str):

    files = dbx.files_list_folder(directory)

    def process_entries(entries):
        for entry in entries:
            print(entry.path_display)

    process_entries(files.entries)

    while files.has_more:
        files = dbx.files_list_folder_continue(files.cursor)

        process_entries(files.entries)

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

if __name__ == '__main__':

    with open('config.json', 'r+') as json_file:
        json_data = json.load(json_file)
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

        


    # Check for an access token
    # if (len(TOKEN) == 0):
    #     sys.exit("ERROR: Looks like you didn't add your access token. "
    #         "Open up backup-and-restore-example.py in a text editor and "
    #         "paste in your token in line 14.")

    print_list_of_paths('')