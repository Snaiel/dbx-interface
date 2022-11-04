from package.model.interface_model import InterfaceModel
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

    def perform_action(self, action: str, **kwargs):
        ACTION_FUNC = {
            'delete': self.delete,
            'move': self.move,
            'open': self.open_path,
            'download': self.download
        }

        thread = threading.Thread(target=ACTION_FUNC[action], kwargs=kwargs, daemon=True)
        thread.start()

    def delete(self, path: str) -> None:
        self.action_update.emit(self, f"deleting {path}")
        self.dbx.files_delete(path)
        self.action_update.emit(self, f"finished deleting {path}")

    def move(self, path: str, new_path: str) -> None:
        self.action_update.emit(self, f"moving {path}")
        self.dbx.files_move(path, new_path)
        self.action_update.emit(self, f"finished moving {path}")

    def open_path(self, path: str) -> None:
        self.action_update.emit(self, f"opening {path}")
        webbrowser.open(f"https://www.dropbox.com/home{path}")
        self.action_update.emit(self, f"opened {path}")

    def download(self, path: str, local_path: str) -> None:
        self.action_update.emit(self, f"downloading {path}")
        # Checks if the path is a file or folder
        if isinstance(self.dbx.files_get_metadata(path), FileMetadata):
            self.dbx.files_download_to_file(local_path, path)
        else:
            local_path += ".zip"
            self.dbx.files_download_zip_to_file(local_path, path)
        self.action_update.emit(self, f"finished downloading {path}")