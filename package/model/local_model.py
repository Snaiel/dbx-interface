import datetime
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import colorama
import pathspec
import pytz

from package.model.dbx_model import DropboxModel
from package.model.interface_model import (ExplorerTask, InterfaceModel,
                                           MyThread)
from package.utils import TIMESTAMP_FORMAT, read_config

colorama.init(autoreset=True)  # Automatically reset colors after each print

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
            'delete_local': self.delete_local,
            'delete_local_and_cloud': self.delete_local_and_cloud,
            'rename': self.rename,
            'open': self.open_path,
            'sync': self.sync,
            'mark_as_synced': self.mark_as_synced
        }

        thread = MyThread(self, ACTION_FUNC[task.action], [task])
        return thread

    def status_update(func):
        return InterfaceModel.status_update(func)

    @status_update
    def create_folder(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        os.mkdir(path)
        self.refresh()

    def _delete_local(self, path):
        config = read_config()
        synced_paths: dict = config["TIME_LAST_SYNCED_FROM_LOCAL"]

        relative_path = "/" + os.path.relpath(path, self.local_root)

        if os.path.isfile(path):
            os.remove(path)
            if relative_path in synced_paths:
                synced_paths.pop(relative_path)
        else:
            shutil.rmtree(path)
            keys_to_remove = [key for key in synced_paths.keys() if key.startswith(relative_path)]
            for key in keys_to_remove:
                synced_paths.pop(key)

        self._write_to_synced_paths(synced_paths)

    @status_update
    def delete_local(self, task: ExplorerTask) -> None:
        path = task.kwargs['path']
        self._delete_local(path)
        self.refresh()

    @status_update
    def delete_local_and_cloud(self, task: ExplorerTask) -> None:
        path: str = task.kwargs['path']
        self._delete_local(path)
        self.dbx_model.api_delete(path.removeprefix(self.local_root))
        self.refresh()

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
    def mark_as_synced(self, task: ExplorerTask) -> None:
        path: str = task.kwargs['path']
        is_file: bool = task.kwargs['is_file']            

        config = read_config()
        synced_paths: dict = config["TIME_LAST_SYNCED_FROM_LOCAL"]
        time_zone: str = config["TIME_ZONE"]

        current_time = datetime.datetime.now()
        current_time = current_time.replace(microsecond=0)
        tz = pytz.timezone(time_zone)
        current_time = tz.localize(current_time)
        current_time_formatted = current_time.strftime(TIMESTAMP_FORMAT)

        if is_file:
            file_relative_path = "/" + os.path.relpath(path, self.local_root)
            synced_paths[file_relative_path] = current_time_formatted
        else:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_local_path = os.path.join(dirpath, filename)
                    file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)
                    synced_paths[file_relative_path] = current_time_formatted
        
        self._write_to_synced_paths(synced_paths)


    @staticmethod
    def _get_applicable_gitignores(path: str, gitignore_stack: list[tuple[str, pathspec.PathSpec]]) -> list:
        applicable: Callable[[str], bool] = []

        for gitignore_path, gitignore_match in gitignore_stack:
            if path.startswith(os.path.dirname(gitignore_path)):
                applicable.append(gitignore_match)

        return applicable

    @status_update
    def sync(self, task: ExplorerTask) -> None:
        config = read_config()
        synced_paths: dict = config["TIME_LAST_SYNCED_FROM_LOCAL"]
        dbx_ignore: set = config["DBX_IGNORE"]
        gitignore_overrides: set = config["GITIGNORE_OVERRIDES"]
        time_zone: str = config["TIME_ZONE"]

        gitignore_stack: list[tuple[str, pathspec.PathSpec]] = []
        applicable_gitignores: list[pathspec.PathSpec] = []

        ignored_directories: list[str] = []
        ignored_dirs_stack: list[int] = []

        dirpath: str
        dirnames: list[str]
        filenames: list[str]

        last_dbx_ignored: str = None

        for dirpath, dirnames, filenames in os.walk(self.local_root):
            # Checks if the current directory is in ignored_directories.
            # If so, continue to next directory
            skip_dir = False
            for dir in ignored_directories:
                if dirpath.startswith(dir):
                    skip_dir = True
                    break
            if skip_dir:
                continue
            
            if last_dbx_ignored and dirpath.startswith(last_dbx_ignored):
                print(colorama.Fore.CYAN + "Ignoring folder in DBX_IGNORE:", "/" + os.path.relpath(dirpath, self.local_root))
                continue

            skip = False
            for ignored in config["DBX_IGNORE"]:
                if dirpath.startswith(ignored):
                    last_dbx_ignored = dirpath
                    skip = True
                    break
            if skip:
                print(colorama.Fore.CYAN + "Ignoring folder in DBX_IGNORE:", "/" + os.path.relpath(dirpath, self.local_root))
                continue

            override_gitignore = False
            for override in gitignore_overrides:
                if dirpath.startswith(override):
                    override_gitignore = True
                    break

            # consider gitignore files
            if '.gitignore' in filenames:
                gitignore_path = os.path.join(dirpath, '.gitignore')
                print(colorama.Fore.CYAN + "Found .gitignore: " + gitignore_path)
                with open(gitignore_path) as file:
                    spec = pathspec.GitIgnoreSpec.from_lines(file.readlines())
                    gitignore_stack.append((gitignore_path, spec))

                new_ignored_dicts = []

                for dirname in dirnames:
                    dir_local_path = os.path.join(dirpath, dirname)
                    if spec.match_file(dirname) and dir_local_path not in gitignore_overrides and not override_gitignore:
                        new_ignored_dicts.append(dir_local_path)
                        print(colorama.Fore.CYAN + "Ignoring folder in .gitignore:", os.path.join(dirpath, dirname))

                ignored_directories.extend(new_ignored_dicts)
                ignored_dirs_stack.append(len(new_ignored_dicts))

                for filename in filenames:
                    # construct the full local path
                    file_local_path = os.path.join(dirpath, filename)
                    file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)

                    sync_file = True

                    if file_local_path in dbx_ignore:
                        print(colorama.Fore.CYAN + "Ignoring file in DBX_IGNORE:", file_relative_path)
                        sync_file = False

                    if spec.match_file(filename) and file_local_path not in gitignore_overrides and not override_gitignore:
                        print(colorama.Fore.CYAN + "Ignoring file in .gitignore:", file_relative_path)
                        sync_file = False

                    if sync_file:
                        self._sync_file(file_local_path, file_relative_path, synced_paths, time_zone)
            else:
                applicable_gitignores = self._get_applicable_gitignores(dirpath, gitignore_stack)

                for dirname in dirnames:
                    dir_local_path = os.path.join(dirpath, dirname)
                    for gitignore_match in applicable_gitignores:
                        if gitignore_match.match_file(dir_local_path) and dir_local_path not in gitignore_overrides and not override_gitignore:
                            ignored_directories.append(dir_local_path)
                            print(colorama.Fore.CYAN + "Ignoring folder in .gitignore:", dir_local_path)

                for filename in filenames:
                    # construct the full local path
                    file_local_path = os.path.join(dirpath, filename)
                    file_relative_path = "/" + os.path.relpath(file_local_path, self.local_root)

                    sync_file = True

                    if file_local_path in dbx_ignore:
                        print(colorama.Fore.CYAN + "Ignoring file in DBX_IGNORE:", file_relative_path)
                        sync_file = False

                    # Check if file is in a gitignore
                    for gitignore_match in applicable_gitignores:
                        if gitignore_match.match_file(file_local_path) and file_local_path not in gitignore_overrides and not override_gitignore:
                            print(colorama.Fore.CYAN + "Ignoring file in .gitignore:", file_relative_path)
                            sync_file = False
                            break

                    if sync_file:
                        self._sync_file(file_local_path, file_relative_path, synced_paths, time_zone)

            # Remove the top .gitignore file from the stack when leaving the directory
            if gitignore_stack and not dirpath.startswith(os.path.dirname(gitignore_stack[-1][0])):
                # print(colorama.Back.RED + dirpath + " " + gitignore_stack[-1][0])
                gitignore_stack.pop()
                ignored_directories = ignored_directories[:-ignored_dirs_stack.pop()]

        # sort paths
        synced_paths = {key:synced_paths[key] for key in sorted(synced_paths.keys())}
        self._write_to_synced_paths(synced_paths)

        self.refresh()

    def _sync_file(self, file_local_path: str, file_relative_path: str, synced_paths: dict[str, str], time_zone: str):
        modified_timestamp = os.path.getmtime(file_local_path)
        # Convert the timestamp to a datetime object
        modified_dt = datetime.datetime.fromtimestamp(modified_timestamp)
        modified_dt = modified_dt.replace(microsecond=0)
        tz = pytz.timezone(time_zone)
        modified_dt = tz.localize(modified_dt)
        # Format the datetime object as a string
        modified_formatted = modified_dt.strftime(TIMESTAMP_FORMAT)


        if file_relative_path in synced_paths:
            modified_synced = datetime.datetime.strptime(synced_paths[file_relative_path], TIMESTAMP_FORMAT)
            if modified_synced < modified_dt:
                success = self.dbx_model.api_upload_file(file_local_path, file_relative_path)
                if success:
                    synced_paths[file_relative_path] = modified_formatted
                    self._write_to_synced_paths(synced_paths)
            else:
                pass
                # print(colorama.Fore.GREEN + "Didn't need to sync: ", file_relative_path, modified_formatted)
        else:
            success = self.dbx_model.api_upload_file(file_local_path, file_relative_path)
            if success:
                synced_paths[file_relative_path] = modified_formatted
                self._write_to_synced_paths(synced_paths)

    @staticmethod
    def _write_to_synced_paths(synced_paths: dict):
        with open(Path(Path(__file__).parents[2], 'config.json'), 'r+') as json_file:
            json_data = json.load(json_file)
            json_data['TIME_LAST_SYNCED_FROM_LOCAL'] = synced_paths

            json_file.seek(0)
            json.dump(json_data, json_file, indent=4)
            json_file.truncate()