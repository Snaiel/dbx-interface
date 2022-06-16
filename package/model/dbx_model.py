from package.model.interface_model import InterfaceModel
from dropbox import Dropbox
from dropbox.files import FileMetadata
import webbrowser

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

    def delete(self, path: str) -> None:
        self.dbx.files_delete(path)

    def move(self, path: str, new_path: str) -> None:
        self.dbx.files_move(path, new_path)

    def open_path(self, path: str) -> None:
        webbrowser.open(f"https://www.dropbox.com/home{path}")