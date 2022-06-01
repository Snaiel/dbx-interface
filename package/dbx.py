"""
This module accesses Dropbox
Takes care of auth and gets the files & folders
"""

import sys
import os
import requests
import json
import dropbox
from dropbox.exceptions import AuthError

def get_list_of_paths(root):

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

    file_list = [{'path':i.path_display, 'is_file':isinstance(i, dropbox.files.FileMetadata)} for i in file_list]

    return file_list

def print_list_of_paths(directory):

    files = dbx.files_list_folder(directory)

    def process_entries(entries):
        for entry in entries:
            print(entry.path_display)

    process_entries(files.entries)

    while files.has_more:
        files = dbx.files_list_folder_continue(files.cursor)

        process_entries(files.entries)

if __name__ == '__main__':

    # Create an instance of a Dropbox class, which can make requests to the API.
    dbx = dropbox.Dropbox(oauth2_access_token=ACCESS_TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError:
        sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

    # data = {
    #     'code': '',
    #     'grant_type': 'authorization_code',
    # }

    # r = requests.post('https://api.dropbox.com/oauth2/token', data=data, auth=(APP_KEY, APP_SECRET))
    # print(r.text)


    # Check for an access token
    # if (len(TOKEN) == 0):
    #     sys.exit("ERROR: Looks like you didn't add your access token. "
    #         "Open up backup-and-restore-example.py in a text editor and "
    #         "paste in your token in line 14.")

    print_list_of_paths('')