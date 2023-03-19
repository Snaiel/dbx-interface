from pathlib import Path
import os, platform, subprocess, threading
from package.model.interface_model import InterfaceModel, ExplorerTask, TaskItemStatus

class LocalModel(InterfaceModel):
    def __init__(self) -> None:
        super().__init__()

    def get_list_of_paths(self, directory: str) -> list:
        file_list = []

        for p in Path(directory).iterdir():
            file_list.append((str(p.resolve()), p.is_file()))

        file_list.sort(key=lambda item: item[0].split("/")[-1].lower())

        return file_list

    def perform_task(self, task: ExplorerTask):

        ACTION_FUNC = {
            'create_folder': self.create_folder,
            'delete': self.delete,
            'rename': self.rename,
            'open': self.open_path,
        }

        thread = threading.Thread(target=ACTION_FUNC[task.action], args=[task], daemon=True)
        thread.start()

    def add_status_updates(func):
        return super().add_status_updates()

    @add_status_updates
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        os.mkdir(path)

    @add_status_updates
    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        if os.path.isfile(path):
            os.remove(path)
        else:
            os.rmdir(path)

    @add_status_updates
    def rename(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        os.rename(path, new_path)

    @add_status_updates
    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        if platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])