from curses import newpad
from pathlib import Path
import os

def get_list_of_paths(directory: str) -> list:
    file_list = []

    for p in Path(directory).iterdir():
        file_list.append((str(p.resolve()), p.is_file()))

    file_list.sort(key=lambda item: item[0].split("/")[-1])

    return file_list

def delete(path: str) -> None:
    if os.path.isfile(path):
        os.remove(path)
    else:
        os.rmdir(path)

def rename(path: str, new_name: str) -> None:
    new_path = path.split("/")
    new_path = new_path[:-1]
    new_path.append(new_name)
    new_path = "/".join(new_path)
    os.rename(path, new_path)