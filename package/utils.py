"""
This module accesses Dropbox
Takes care of auth and gets the files & folders
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytz
import requests
from dropbox import Dropbox
from dropbox.exceptions import AuthError

PROJECT_ROOT = Path(__file__).parents[1]
CONFIG_PATH = Path(PROJECT_ROOT, 'config.json')

OLD_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S%z"

def create_dbx() -> Dropbox:
    with open(CONFIG_PATH, 'r+') as json_file:
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

def create_config(code: str, app_key: str, app_secret: str, dropbox_location: str, time_zone: str) -> None:
    data = {
        'code': code,
        'grant_type': 'authorization_code',
    }

    r = requests.post('https://api.dropbox.com/oauth2/token', data=data, auth=(app_key, app_secret))
    r_data = r.json()

    config_data = {
        'DROPBOX_LOCATION': dropbox_location,
        'TIME_ZONE': time_zone,
        'APP_KEY': app_key,
        'APP_SECRET': app_secret,
        'ACCESS_TOKEN': r_data["access_token"],
        'REFRESH_TOKEN': r_data["refresh_token"],
        'GITIGNORE_OVERRIDES': [],
        'TIME_LAST_SYNCED_FROM_CLOUD': {},
        'TIME_LAST_SYNCED_FROM_LOCAL': {}
    }

    with open(CONFIG_PATH, "w") as json_file:
        json.dump(config_data, json_file, indent=4)

def read_config() -> dict:
    with open(CONFIG_PATH, 'r') as json_file:
        config_data = json.load(json_file)
        if 'GITIGNORE_OVERRIDES' not in config_data:
            config_data['GITIGNORE_OVERRIDES'] = set()
        else:
            config_data['GITIGNORE_OVERRIDES'] = set(config_data['GITIGNORE_OVERRIDES'])

        if "TIME_LAST_SYNCED_FROM_LOCAL" not in config_data:
            config_data["TIME_LAST_SYNCED_FROM_LOCAL"] = dict()
        
        if "TIME_LAST_SYNCED_FROM_CLOUD" not in config_data:
            config_data["TIME_LAST_SYNCED_FROM_CLOUD"] = dict()

        return config_data
    
def clean_synced_paths(local_dbx_path: str) -> None:
    print("Cleaning TIME_LAST_SYNCED_FROM_LOCAL")
    files = []

    for dirpath, dirnames, filenames in os.walk(local_dbx_path):
        for filename in filenames:
            file_local_path = os.path.join(dirpath, filename)
            file_relative_path = "/" + os.path.relpath(file_local_path, local_dbx_path)
            files.append(file_relative_path)

    config: dict = read_config()

    if "SYNCED_PATHS" in config:
        if "TIME_LAST_SYNCED_FROM_LOCAL" not in config:
            print("Changing SYNCED_PATHS to TIME_LAST_SYNCED_FROM_LOCAL")
            config["TIME_LAST_SYNCED_FROM_LOCAL"] = config["SYNCED_PATHS"]
        config.pop("SYNCED_PATHS")

    config["TIME_LAST_SYNCED_FROM_LOCAL"] = {key: value for key, value in config["TIME_LAST_SYNCED_FROM_LOCAL"].items() if key in files}

    config['GITIGNORE_OVERRIDES'] = list(config['GITIGNORE_OVERRIDES'])

    config['TIME_LAST_SYNCED_FROM_CLOUD'] = config.pop("TIME_LAST_SYNCED_FROM_CLOUD")
    config['TIME_LAST_SYNCED_FROM_LOCAL'] = config.pop("TIME_LAST_SYNCED_FROM_LOCAL")

    # convert any old timestamp to use time zones
    convert_to_time_zone_format(config, 'TIME_LAST_SYNCED_FROM_CLOUD')
    convert_to_time_zone_format(config, 'TIME_LAST_SYNCED_FROM_LOCAL')

    with open(CONFIG_PATH, 'w') as json_file:
        json.dump(config, json_file, indent=4)


def convert_to_time_zone_format(config: dict, synced_times_key: str):
    for path, timestamp_str in config[synced_times_key].items():
        try:
            timestamp_datetime = datetime.strptime(timestamp_str, OLD_TIMESTAMP_FORMAT)
            tz = pytz.timezone(config["TIME_ZONE"])
            timestamp_datetime_tz = tz.localize(timestamp_datetime)
            config[synced_times_key][path] = timestamp_datetime_tz.strftime(TIMESTAMP_FORMAT)
        except ValueError as e:
            # correct time zone format
            pass