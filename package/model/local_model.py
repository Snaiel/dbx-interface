from pathlib import Path
import os
import platform
import subprocess
from package.model.interface_model import InterfaceModel

class LocalModel(InterfaceModel):
    def __init__(self) -> None:
        super().__init__()

    def get_list_of_paths(self, directory: str) -> list:
        file_list = []

        for p in Path(directory).iterdir():
            file_list.append((str(p.resolve()), p.is_file()))

        file_list.sort(key=lambda item: item[0].split("/")[-1].lower())

        return file_list

    def delete(self, path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)
        else:
            os.rmdir(path)

    def move(self, path: str, new_path: str) -> None:
        os.rename(path, new_path)

    def open_path(self, path: str) -> None:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])