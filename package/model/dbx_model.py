from package.model.interface_model import InterfaceModel, ExplorerTask, TaskItemStatus
from dropbox import Dropbox
from dropbox.files import FileMetadata, UploadSessionStartResult, UploadSessionCursor, CommitInfo
import webbrowser, threading, os

class DropboxModel(InterfaceModel):

    MAX_BUCKET_SIZE = 50 # in megabytes

    def __init__(self, dbx) -> None:
        super().__init__()
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
            'upload': self.upload
        }

        thread = threading.Thread(target=ACTION_FUNC[task.action], args=[task], daemon=True)
        thread.start()

    def add_status_updates(func):
        return super().add_status_updates()

    @add_status_updates
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_create_folder(path, True)

    @add_status_updates
    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_delete(path)

    @add_status_updates
    def move(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        self.dbx.files_move(path, new_path)

    @add_status_updates
    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        webbrowser.open(f"https://www.dropbox.com/home{path}")

    @add_status_updates
    def download(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        local_path = task.kwargs['local_path']

        # Checks if the path is a file or folder
        if isinstance(self.dbx.files_get_metadata(path), FileMetadata):
            self.dbx.files_download_to_file(local_path, path)
        else:
            local_path += ".zip"
            self.dbx.files_download_zip_to_file(local_path, path)

    @add_status_updates
    def upload(self, task: ExplorerTask) -> None:
        BYTES_TO_MEGABYTES = 1000 ** 2
        MAX_BUCKET_SIZE_BYTES = BYTES_TO_MEGABYTES * self.MAX_BUCKET_SIZE

        path = task.kwargs['path']
        dbx_path = task.kwargs['dbx_path']

        file_size = os.path.getsize(path)

        print(f"file size: {file_size / BYTES_TO_MEGABYTES}")

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

        # TODO: folder uploads and multiple files