import os, platform, subprocess, threading, datetime, json
from pathlib import Path
from package.model.interface_model import InterfaceModel, ExplorerTask
from package.model.dbx_model import DropboxModel
from package.utils import read_config

class LocalModel(InterfaceModel):
    def __init__(self, local_root, dbx_model: DropboxModel) -> None:
        super().__init__(local_root)
        self.dbx_model = dbx_model

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
            'sync': self.sync
        }

        thread = threading.Thread(target=ACTION_FUNC[task.action], args=[task], daemon=True)
        thread.start()

    def status_update(func):
        return InterfaceModel.status_update(func)

    @status_update
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        os.mkdir(path)

    @status_update
    def delete(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        if os.path.isfile(path):
            os.remove(path)
        else:
            os.rmdir(path)

    @status_update
    def rename(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        new_path = task.kwargs['new_path']
        os.rename(path, new_path)

    @status_update
    def open_path(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        if platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    @status_update
    def sync(self, task: ExplorerTask) -> None:
        synced_paths = read_config()["SYNCED_PATHS"]

        FORMAT = "%Y-%m-%d %H:%M:%S"
        for dirpath, dirnames, filenames in os.walk(self.local_root):
            for filename in filenames:
                # construct the full local path
                file_local_path = os.path.join(dirpath, filename)
                file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)

                modified_timestamp = os.path.getmtime(file_local_path)
                # Convert the timestamp to a datetime object
                modified_dt = datetime.datetime.fromtimestamp(modified_timestamp)
                modified_dt = modified_dt.replace(microsecond=0)
                # Format the datetime object as a string
                modified_formatted = modified_dt.strftime(FORMAT)

                if file_relative_path in synced_paths:
                    modified_synced = datetime.datetime.strptime(synced_paths[file_relative_path], FORMAT)
                    if modified_synced < modified_dt:
                        synced_paths[file_relative_path] = modified_formatted
                        self.dbx_model.upload_file(ExplorerTask('upload_file', path=file_local_path, dbx_path=file_relative_path, from_folder=True))
                    else:
                        print("Didn't need to sync: ", file_relative_path, modified_formatted)
                else:
                    synced_paths[file_relative_path] = modified_formatted
                    self.dbx_model.upload_file(ExplorerTask('upload_file', path=file_local_path, dbx_path=file_relative_path, from_folder=True))

        with open(Path(Path(__file__).parents[2], 'config.json'), 'r+') as json_file:
            json_data = json.load(json_file)
            json_data['SYNCED_PATHS'] = synced_paths

            json_file.seek(0)
            json.dump(json_data, json_file, indent=4)
            json_file.truncate()

        self.refresh()