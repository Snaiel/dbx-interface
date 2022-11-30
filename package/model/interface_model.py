from PyQt5.QtCore import pyqtSignal, QObject
from enum import Enum

class TaskItemStatus(Enum):
    QUEUED = 1
    RUNNING = 2
    DONE = 3

class ExplorerTask(QObject):
    action_update = pyqtSignal(TaskItemStatus)

    def __init__(self, action: str, **kwargs) -> None:
        super().__init__()
        self.action = action
        self.kwargs = kwargs

class InterfaceModel(QObject):

    def __init__(self) -> None:
        super().__init__()

    def get_list_of_paths(self, directory: str) -> list:
        '''
        retrieves a list of files and folders given a directory path
        '''

    def perform_task(self, task: ExplorerTask):
        '''
        performs a given action using multithreading
        '''

    def delete(self, task: ExplorerTask) -> None:
        '''
        delete the item at the specified path
        '''

    def move(self, task: ExplorerTask) -> None:
        '''
        move the item from the specified path to new_path
        '''

    def open_path(self, task: ExplorerTask) -> None:
        '''
        open the path for viewing
        '''