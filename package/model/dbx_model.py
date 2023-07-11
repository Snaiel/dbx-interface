from package.model.interface_model import InterfaceModel, ExplorerTask
from dropbox import Dropbox
from dropbox.files import FileMetadata, UploadSessionStartResult, UploadSessionCursor, CommitInfo, ListFolderResult
from dropbox.exceptions import ApiError
import webbrowser, threading, os, json, datetime, zipfile
from pathlib import Path

class DropboxModel(InterfaceModel):

    MAX_BUCKET_SIZE = 50 # in megabytes

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

    def perform_task(self, task: ExplorerTask):
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

        thread = threading.Thread(target=ACTION_FUNC[task.action], args=[task], daemon=True)
        thread.start()

    def status_update(func):
        return InterfaceModel.status_update(func)

    @status_update
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_create_folder(path, True)

    @status_update
    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_delete(path)

    @status_update
    def move(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        self.dbx.files_move(path, new_path)

    @status_update
    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        webbrowser.open(f"https://www.dropbox.com/home{path}")

    @status_update
    def download(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        local_path = task.kwargs['local_path']

        # Checks if the path is a file or folder
        if isinstance(self.dbx.files_get_metadata(path), FileMetadata):
            self.dbx.files_download_to_file(local_path, path)
        else:
            local_path += ".zip"
            self.dbx.files_download_zip_to_file(local_path, path)

    @status_update
    def upload_file(self, task: ExplorerTask) -> None:
        BYTES_TO_MEGABYTES = 1000 ** 2
        MAX_BUCKET_SIZE_BYTES = BYTES_TO_MEGABYTES * self.MAX_BUCKET_SIZE

        path = task.kwargs['path']
        dbx_path = task.kwargs['dbx_path']

        file_size = os.path.getsize(path)

        print(f"Uploading '{path}' file size: {file_size / BYTES_TO_MEGABYTES}")

        try:
            if (file_size / BYTES_TO_MEGABYTES) < self.MAX_BUCKET_SIZE:
                with open(path, 'rb') as file:
                    data = file.read()
                    self.dbx.files_upload(data, dbx_path)
            else:
                with open(path, 'rb') as file:
                    session_start_result : UploadSessionStartResult = self.dbx.files_upload_session_start(None)

                    bucket_size_bytes = MAX_BUCKET_SIZE_BYTES
                    session_cursor = UploadSessionCursor(session_start_result.session_id, 0)
                    commit_info = CommitInfo(dbx_path)

                    number_of_buckets = int((file_size / MAX_BUCKET_SIZE_BYTES) + 1)
                    last_append_size = file_size % MAX_BUCKET_SIZE_BYTES
                    
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

                        print(session_cursor.offset)

                    print("finish up")

                    self.dbx.files_upload_session_finish(None, session_cursor, commit_info)

            if 'from_folder' not in task.kwargs:
                self.refresh()
        
        except ApiError as e:
            print(f"Failed to upload '{path}' ({e})")

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
                self.upload_file(ExplorerTask('upload_file', path=file_local_path, dbx_path=file_dropbox_path, from_folder=True))

        self.refresh()

    @status_update
    def sync(self, task: ExplorerTask):
        local_path = task.kwargs['local_path']
        dbx_path = task.kwargs['dbx_path']
        if Path(dbx_path).suffix:
            self.sync_file(local_path, dbx_path)
        else:
            self.sync_folder(local_path, dbx_path)
        self.refresh()

    def sync_file(self, local_path: str, dbx_path: str) -> None:
        display_path = self.dbx.files_get_metadata(dbx_path).path_display
        file_local_path = Path(local_path, display_path[1:])
        if not os.path.exists(file_local_path.parent):
            os.makedirs(file_local_path.parent)
            print("Downloading", file_local_path)
            self.dbx.files_download_to_file(file_local_path, dbx_path)
        self.update_synced_paths(local_path, [display_path])

    def sync_folder(self, local_path: str, dbx_path: str) -> None:
        display_path = self.dbx.files_get_metadata(dbx_path).path_display
        folder_local_path = Path(local_path, display_path[1:])

        if not os.path.exists(folder_local_path.parent):
            os.makedirs(folder_local_path.parent)

        zip_path = str(folder_local_path) + ".zip"
        print("Downloading", folder_local_path)
        self.dbx.files_download_zip_to_file(zip_path, dbx_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(folder_local_path.parent)

        files = []

        for dirpath, dirnames, filenames in os.walk(folder_local_path):
            for filename in filenames:
                # construct the full local path
                file_local_path = os.path.join(dirpath, filename)
                file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)
                files.append(file_relative_path)

        self.update_synced_paths(local_path, files)

        os.remove(zip_path)

    def update_synced_paths(self, local_path: str, new_paths: list):
        with open(Path(Path(__file__).parents[2], 'config.json'), 'r+') as json_file:
            json_data = json.load(json_file)

            new_entries = {}

            for path in new_paths:
                file_local_path = Path(local_path, path[1:])
                modified_timestamp = os.path.getmtime(file_local_path)
                # Convert the timestamp to a datetime object
                modified_dt = datetime.datetime.fromtimestamp(modified_timestamp)
                modified_dt = modified_dt.replace(microsecond=0)
                # Format the datetime object as a string
                modified_formatted = modified_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                new_entries[path] = modified_formatted

            json_data['SYNCED_PATHS'].update(new_entries)
            json_file.seek(0)
            json.dump(json_data, json_file, indent=4)
            json_file.truncate()