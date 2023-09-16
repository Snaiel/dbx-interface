import datetime
import json
import os
import threading
import webbrowser
import zipfile
from pathlib import Path
from pprint import pprint
from time import sleep

import colorama
import pytz
from dropbox import Dropbox
from dropbox.exceptions import ApiError
from dropbox.files import (CommitInfo, FileMetadata, FolderMetadata,
                           UploadSessionCursor, UploadSessionStartResult,
                           WriteMode)

from package.model.interface_model import (ExplorerTask, InterfaceModel,
                                           MyThread)
from package.utils import read_config

colorama.init(autoreset=True)

class DropboxModel(InterfaceModel):

    MAX_BUCKET_SIZE = 50 # in megabytes
    BYTES_TO_MEGABYTES = 1000 ** 2
    MAX_BUCKET_SIZE_BYTES = BYTES_TO_MEGABYTES * MAX_BUCKET_SIZE

    def __init__(self, local_root, dbx) -> None:
        super().__init__(local_root)
        self.dbx = dbx #type: Dropbox


    def get_list_of_paths(self, root: str) -> list:
        file_list = []
        files = self.dbx.files_list_folder(root)

        def process_entries(entries):
            for entry in entries:
                file_list.append(entry)

        process_entries(files.entries)

        while files.has_more:
            files = self.dbx.files_list_folder_continue(files.cursor)

            process_entries(files.entries)

        file_list.sort(key= lambda x: x.path_lower)
        file_list = [(i.path_display, isinstance(i, FileMetadata)) for i in file_list]

        return file_list


    def perform_task(self, task: ExplorerTask) -> MyThread:
        ACTION_FUNC = {
            'create_folder': self.create_folder,
            'delete': self.delete,
            'rename': self.move,
            'open': self.open_path,
            'download': self.download,
            'upload_file': self.upload_file,
            'upload_folder': self.upload_folder,
            'sync': self.sync
        }

        thread = MyThread(self, ACTION_FUNC[task.action], [task])
        return thread


    def status_update(func):
        return InterfaceModel.status_update(func)


    @status_update
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_create_folder(path, True)
        self.refresh()

    def api_delete(self, path: str) -> None:
        self.dbx.files_delete(path)

    @status_update
    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.api_delete(path)

    @status_update
    def move(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        self.dbx.files_move(path, new_path)


    @status_update
    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        webbrowser.open(f"https://www.dropbox.com/home{path}")


    def _get_dbx_folder_size(self, path: str, info: dict) -> int:
        """
        recursive function to retrieve folder size in bytes
        """
        size = 0
        folders = []
        files = []

        if info["finished"]:
            return size

        for entry in self.dbx.files_list_folder(path).entries:
            if type(entry) == FolderMetadata:
                folders.append(entry)
            elif type(entry) == FileMetadata:
                files.append(entry)

        for subfolder in folders:
            subfolder_path = path + "/" + subfolder.name
            size += self._get_dbx_folder_size(subfolder_path, info)

        for file in files:
            size += file.size

        return size


    def _download_progress(self, info: dict):
        dbx_path = info["dbx_path"]
        local_path = info["local_path"]
        if info["is_file"]:
            total = self.dbx.files_get_metadata(dbx_path).size
        else:
            print(colorama.Fore.MAGENTA + "Retrieving folder size...")
            total = self._get_dbx_folder_size(dbx_path, info)

        if not info["finished"]:
            print(colorama.Fore.MAGENTA + f"Download size: ({total / self.BYTES_TO_MEGABYTES:.2f} MB)")

        while True:
            if info["finished"]:
                return
            
            if not os.path.exists(local_path):
                sleep(2)
                continue

            current_download_mb = os.path.getsize(local_path) / self.BYTES_TO_MEGABYTES
            total_mb = total / self.BYTES_TO_MEGABYTES
            percentage = int(current_download_mb / total_mb * 100)

            print(colorama.Fore.MAGENTA + f"Download Progress: {current_download_mb:.2f}/{total_mb:.2f} MB ({percentage}%)")
            sleep(10)


    @status_update
    def download(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        local_path = task.kwargs['local_path']

        if os.path.exists(local_path):
            os.remove(local_path)

        is_file = isinstance(self.dbx.files_get_metadata(path), FileMetadata)
        if not is_file:
            local_path += ".zip"

        info = {
            "dbx_path": path,
            "local_path": local_path,
            "is_file": is_file,
            "finished": False
        }

        print(colorama.Fore.MAGENTA + f"Downloading \"{path}\" to \"{local_path}\"")

        download_progress_thread = threading.Thread(target=self._download_progress, args=[info], daemon=True)
        download_progress_thread.start()

        if is_file:
            self.dbx.files_download_to_file(local_path, path)
        else:
            self.dbx.files_download_zip_to_file(local_path, path)

        print(colorama.Fore.MAGENTA + f"Download Finished")
        info["finished"] = True


    @status_update
    def upload_file(self, task: ExplorerTask) -> bool:
        success = self.api_upload_file(task.kwargs["path"], task.kwargs["dbx_path"])
        if success:
            self.refresh()


    def api_upload_file(self, local_path: str, dbx_path: str) -> bool:
        success = False

        file_size = os.path.getsize(local_path)

        print(colorama.Fore.BLUE + f"Uploading '{local_path}' file size: {file_size / self.BYTES_TO_MEGABYTES}")

        try:
            if (file_size / self.BYTES_TO_MEGABYTES) < self.MAX_BUCKET_SIZE:
                with open(local_path, 'rb') as file:
                    data = file.read()
                    self.dbx.files_upload(data, dbx_path, WriteMode.overwrite)
            else:
                with open(local_path, 'rb') as file:
                    session_start_result : UploadSessionStartResult = self.dbx.files_upload_session_start(None)

                    bucket_size_bytes = self.MAX_BUCKET_SIZE_BYTES
                    session_cursor = UploadSessionCursor(session_start_result.session_id, 0)
                    commit_info = CommitInfo(dbx_path)

                    number_of_buckets = int((file_size / self.MAX_BUCKET_SIZE_BYTES) + 1)
                    last_append_size = file_size % self.MAX_BUCKET_SIZE_BYTES
                    
                    print(f"bucket size: {bucket_size_bytes}")
                    print(f"last append size: {last_append_size}")

                    for i in range(1, number_of_buckets + 1):
                        print(f"uploading bucket {i}/{number_of_buckets}")

                        bucket = file.read(bucket_size_bytes)
                        self.dbx.files_upload_session_append_v2(bucket, session_cursor)

                        if i < number_of_buckets:
                            session_cursor.offset += bucket_size_bytes
                        else:
                            session_cursor.offset += last_append_size

                        # print(session_cursor.offset)

                    print("finish up")

                    self.dbx.files_upload_session_finish(None, session_cursor, commit_info)

            success = True
        
        except ApiError as e:
            print(colorama.Fore.RED + f"Failed to upload '{local_path}' ({e})")

        return success


    @status_update
    def upload_folder(self, task: ExplorerTask):
        path = task.kwargs['path']
        dbx_path = task.kwargs['dbx_path']

        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                # construct the full local path
                file_local_path = os.path.join(dirpath, filename)

                # construct the full Dropbox path
                file_relative_path = os.path.relpath(file_local_path, path)
                file_dropbox_path = os.path.join(dbx_path, file_relative_path)
                self.api_upload_file(file_local_path, file_dropbox_path)

        self.refresh()


    @status_update
    def sync(self, task: ExplorerTask):
        local_path = task.kwargs['local_path']
        dbx_path = task.kwargs['dbx_path']

        config = read_config()

        synced_paths: dict = config["TIME_LAST_SYNCED_FROM_CLOUD"]
        time_zone: str = config["TIME_ZONE"]

        if Path(dbx_path).suffix:
            self.sync_file(local_path, dbx_path, synced_paths, time_zone)
        else:
            self.sync_folder(local_path, dbx_path)
        self.refresh()


    def sync_file(self, local_path: str, dbx_path: str, synced_paths: dict, time_zone: str) -> None:
        """
        local_path: the user's local dropbox location
        dbx_path: the path to the file on the user's dropbox cloud
        """

        dropbox_file_metadata: FileMetadata = self.dbx.files_get_metadata(dbx_path)

        display_path = dropbox_file_metadata.path_display

        tz = pytz.timezone(time_zone)

        last_dropbox_modification_utc_dt: datetime.datetime = dropbox_file_metadata.server_modified
        last_dropbox_modification_utc_dt = pytz.UTC.localize(last_dropbox_modification_utc_dt)

        file_local_path = Path(local_path, display_path[1:])


        download = False
        if display_path in synced_paths:
            last_synced_timestamp = os.path.getmtime(file_local_path)
            # Convert the timestamp to a datetime object
            last_synced_dt = datetime.datetime.fromtimestamp(last_synced_timestamp)
            last_synced_dt = last_synced_dt.replace(microsecond=0)
            last_synced_dt = tz.localize(last_synced_dt)

            if last_synced_dt < last_dropbox_modification_utc_dt:
                download = True
            else:
                print(colorama.Fore.GREEN + "Didn't need to sync/download " + display_path)
        else:
            download = True

        if download:
            if not os.path.exists(file_local_path.parent):
                os.makedirs(file_local_path.parent)

            print(colorama.Fore.MAGENTA + f"Downloading to local Dropbox: \"{dbx_path}\"")
            
            info = {
                "dbx_path": dbx_path,
                "local_path": file_local_path,
                "is_file": True,
                "finished": False
            }

            download_progress_thread = threading.Thread(target=self._download_progress, args=[info], daemon=True)
            download_progress_thread.start()
            
            self.dbx.files_download_to_file(file_local_path, dbx_path)

            print(colorama.Fore.MAGENTA + f"Download Finished")
            info["finished"] = True

            self.update_last_time_synced(local_path, [display_path], False)
            # because we essentially 'modified' the local copy
            self.update_last_time_synced(local_path, [display_path])


    def sync_folder(self, local_path: str, dbx_path: str) -> None:
        """
        local_path: the user's local dropbox location
        dbx_path: the path to the folder on the user's dropbox cloud
        """

        display_path = self.dbx.files_get_metadata(dbx_path).path_display
        folder_local_path = Path(local_path, display_path[1:])

        if not os.path.exists(folder_local_path.parent):
            os.makedirs(folder_local_path.parent)

        zip_path = str(folder_local_path) + ".zip"

        print(colorama.Fore.MAGENTA + f"Downloading to local Dropbox: \"{dbx_path}\"")
        info = {
            "dbx_path": dbx_path,
            "local_path": zip_path,
            "is_file": False,
            "finished": False
        }
        download_progress_thread = threading.Thread(target=self._download_progress, args=[info], daemon=True)
        download_progress_thread.start()

        self.dbx.files_download_zip_to_file(zip_path, dbx_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(folder_local_path.parent)

        print(colorama.Fore.MAGENTA + f"Download Finished")
        info["finished"] = True

        files = []

        for dirpath, dirnames, filenames in os.walk(folder_local_path):
            for filename in filenames:
                # construct the full local path
                file_local_path = os.path.join(dirpath, filename)
                file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)
                files.append(file_relative_path)

        self.update_last_time_synced(local_path, files)

        os.remove(zip_path)

    def update_last_time_synced(self, local_path: str, new_paths: list[str], local: bool = True):
        '''
        puts all the paths in new_paths in TIME_LAST_SYNCED_FROM_LOCAL with their
        modified time.

        local_path: the path to the user's local dropbox folder
        new_paths: the list of paths that correspond to the ones in the cloud
        '''

        if local:
            suffix = "LOCAL"
        else:
            suffix = "CLOUD"

        with open(Path(Path(__file__).parents[2], 'config.json'), 'r+') as json_file:
            json_data = json.load(json_file)

            new_entries = {}

            for path in new_paths:
                file_local_path = Path(local_path, path[1:])
                timestamp = os.path.getmtime(file_local_path)
                # Convert the timestamp to a datetime object
                dt = datetime.datetime.fromtimestamp(timestamp)
                dt = dt.replace(microsecond=0)
                # Format the datetime object as a string
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                new_entries[path] = formatted

            json_data['TIME_LAST_SYNCED_FROM_' + suffix].update(new_entries)
            json_file.seek(0)
            json.dump(json_data, json_file, indent=4)
            json_file.truncate()