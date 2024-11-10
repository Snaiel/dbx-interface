"""
This module accesses Dropbox
Takes care of auth and gets the files & folders
"""

import json
import os
from collections.abc import Iterable
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

        if "DBX_IGNORE" not in config_data:
            config_data["DBX_IGNORE"] = set()
        else:
            config_data["DBX_IGNORE"] = set(config_data["DBX_IGNORE"])

        if "GITIGNORE_OVERRIDES" not in config_data:
            config_data["GITIGNORE_OVERRIDES"] = set()
        else:
            config_data["GITIGNORE_OVERRIDES"] = set(config_data["GITIGNORE_OVERRIDES"])

        if "TIME_LAST_SYNCED_FROM_LOCAL" not in config_data:
            config_data["TIME_LAST_SYNCED_FROM_LOCAL"] = dict()
        
        if "TIME_LAST_SYNCED_FROM_CLOUD" not in config_data:
            config_data["TIME_LAST_SYNCED_FROM_CLOUD"] = dict()

        return config_data
    
def clean_synced_paths(local_dbx_path: str) -> Iterable[str]:

    print("Reading config")
    config: dict = read_config()

    existing_files = set()
    existing_folders = set()

    print("Scanning through local files")
    last_ignored: str = None
    for dirpath, dirnames, filenames in os.walk(local_dbx_path):
        if last_ignored and dirpath.startswith(last_ignored):
            continue

        for ignored in config["DBX_IGNORE"]:
            if dirpath.startswith(ignored):
                last_ignored = dirpath
                continue

        existing_folders.add("/" + os.path.relpath(dirpath, local_dbx_path))
        for filename in filenames:
            file_local_path = os.path.join(dirpath, filename)
            file_relative_path = "/" + os.path.relpath(file_local_path, local_dbx_path)
            existing_files.add(file_relative_path)

    if "SYNCED_PATHS" in config:
        if "TIME_LAST_SYNCED_FROM_LOCAL" not in config:
            print("Changing SYNCED_PATHS to TIME_LAST_SYNCED_FROM_LOCAL")
            config["TIME_LAST_SYNCED_FROM_LOCAL"] = config["SYNCED_PATHS"]
        config.pop("SYNCED_PATHS")

    print("Checking for modified files")
    new_time_last_synced_from_local = {}
    nonexistent_files = set()
    for path, time in config["TIME_LAST_SYNCED_FROM_LOCAL"].items():
        if path in existing_files:
            new_time_last_synced_from_local[path] = time
        else:
            nonexistent_files.add(path)

    print("Checking time zone formatting")
    tz = pytz.timezone(config['TIME_ZONE'])
    for path, time in new_time_last_synced_from_local.items():
        try:
            datetime.strptime(time, TIMESTAMP_FORMAT)
        except ValueError:
            dt = datetime.strptime(time, OLD_TIMESTAMP_FORMAT)
            dt = tz.localize(dt)
            new_time_last_synced_from_local[path] = datetime.strftime(dt, TIMESTAMP_FORMAT)

    config['TIME_LAST_SYNCED_FROM_LOCAL'] = new_time_last_synced_from_local

    config['GITIGNORE_OVERRIDES'] = list(config['GITIGNORE_OVERRIDES'])

    # This may look useless, but removing them and adding them back in again
    # puts them at the bottom of the file so that other attributes can be
    # seen at the top of the config file
    config['TIME_LAST_SYNCED_FROM_CLOUD'] = config.pop("TIME_LAST_SYNCED_FROM_CLOUD")
    config['TIME_LAST_SYNCED_FROM_LOCAL'] = config.pop("TIME_LAST_SYNCED_FROM_LOCAL")

    # convert any old timestamp to use time zones
    convert_to_time_zone_format(config, 'TIME_LAST_SYNCED_FROM_CLOUD')
    convert_to_time_zone_format(config, 'TIME_LAST_SYNCED_FROM_LOCAL')

    config["DBX_IGNORE"] = list(config["DBX_IGNORE"])
    config["GITIGNORE_OVERRIDES"] = list(config["GITIGNORE_OVERRIDES"])

    with open(CONFIG_PATH, 'w') as json_file:
        json.dump(config, json_file, indent=4)

    return find_paths_to_delete(existing_folders, nonexistent_files)


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


def find_paths_to_delete(existing_folders, nonexistent_files) -> set[str]:
    print("Finding any newly deleted files")

    folders_to_delete = set()
    files_to_delete = set()

    for file_path in nonexistent_files:
        # if the file is inside a directory that will be deleted anyway,
        # continue to next file
        if path_inside_path(file_path, folders_to_delete):
            continue

        prev_dir_path = ""
        dir_path = os.path.dirname(file_path)

        if dir_path in existing_folders:
            files_to_delete.add(file_path)
            continue

        # find the dir_path that does exist
        while dir_path not in existing_folders and dir_path != '':
            prev_dir_path = dir_path
            dir_path = os.path.dirname(dir_path)

        # at this point dir_path is a path that exists,
        # so prev_dir_path is the highest dir that does not exist
        if prev_dir_path:
            folders_to_delete.add(prev_dir_path)

    return folders_to_delete.union(files_to_delete)


def path_inside_path(path: str, paths: Iterable[str]):
    for cur_path in paths:
        if path.startswith(cur_path):
            return True
    return False