from pathlib import Path

def get_list_of_paths(directory) -> list:
    file_list = []

    for p in Path(directory).iterdir():
        file_list.append((str(p.resolve()), p.is_file()))

    file_list.sort(key=lambda item: item[0].split("/")[-1])

    return file_list