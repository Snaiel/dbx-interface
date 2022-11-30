from package.model.interface_model import InterfaceModel, ExplorerTask
from dropbox import Dropbox
from dropbox.files import FileMetadata
import webbrowser
import threading

class DropboxModel(InterfaceModel):

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
            'delete': self.delete,
            'move': self.move,
            'open': self.open_path,
            'download': self.download
        }

        thread = threading.Thread(target=ACTION_FUNC[task.action], args=[task], daemon=True)
        thread.start()

    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self.dbx.files_delete(path)

    def move(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        self.dbx.files_move(path, new_path)

    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        webbrowser.open(f"https://www.dropbox.com/home{path}")

    def download(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        local_path = task.kwargs['local_path']

        # Checks if the path is a file or folder
        if isinstance(self.dbx.files_get_metadata(path), FileMetadata):
            self.dbx.files_download_to_file(local_path, path)
        else:
            local_path += ".zip"
            self.dbx.files_download_zip_to_file(local_path, path)