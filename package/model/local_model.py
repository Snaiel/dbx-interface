from pathlib import Path
import os, platform, subprocess, threading
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

    def perform_action(self, action: str, **kwargs):
        ACTION_FUNC = {
            'delete': self.delete,
            'move': self.move,
            'open': self.open_path,
        }

        thread = threading.Thread(target=ACTION_FUNC[action], kwargs=kwargs, daemon=True)
        thread.start()

    def delete(self, path: str) -> None:
        self.action_update.emit(self, f"deleting {path}")
        if os.path.isfile(path):
            os.remove(path)
        else:
            os.rmdir(path)
        self.action_update.emit(self, f"finished deleting {path}")

    def move(self, path: str, new_path: str) -> None:
        self.action_update.emit(self, f"moving {path}")
        os.rename(path, new_path)
        self.action_update.emit(self, f"finished moving {path}")

    def open_path(self, path: str) -> None:
        self.action_update.emit(self, f"opening {path}")
        if platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        self.action_update.emit(self, f"opened {path}")