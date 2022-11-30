from PyQt5.QtCore import pyqtSignal, QObject
from enum import Enum

class TaskItemStatus(Enum):
    QUEUED = 1
    RUNNING = 2
    DONE = 3

class InterfaceModel(QObject):
    action_update = pyqtSignal(QObject, str)

    def __init__(self) -> None:
        super().__init__()

    def get_list_of_paths(self, directory: str) -> list:
        '''
        retrieves a list of files and folders given a directory path
        '''

    def perform_action(self, action: str, **kwargs):
        '''
        performs a given action using multithreading
        '''

    def delete(self, path: str) -> None:
        '''
        delete the item at the specified path
        '''

    def move(self, path: str, new_path: str) -> None:
        '''
        move the item from the specified path to new_path
        '''

    def open_path(self, path: str) -> None:
        '''
        open the path for viewing
        '''

class ExplorerAction(QObject):
    action_update = pyqtSignal(TaskItemStatus)

    def __init__(self, action: str, **kwargs) -> None:
        super().__init__()
        self.action = action
        self.kwargs = kwargs