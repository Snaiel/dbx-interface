from __future__ import annotations

from enum import Enum

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from package.utils import read_config


class TaskItemStatus(Enum):
    QUEUED = 1
    RUNNING = 2
    DONE = 3

class MyThread(QThread):
    def __init__(self, parent, target=None, args=[]):
        super().__init__(parent)
        self.target = target
        self.args = args
    
    def run(self):
        if self.target:
            self.target(*self.args)

class ExplorerTask(QObject):
    task_update = pyqtSignal()

    def __init__(self, action: str, **kwargs) -> None:
        super().__init__()
        self.action = action
        self.status = TaskItemStatus.QUEUED
        self.kwargs = kwargs

    def emit_update(self):
        self.task_update.emit()

class InterfaceModel(QObject):

    refresh_signal = pyqtSignal()

    def __init__(self, local_root) -> None:
        super().__init__()
        self.local_root = local_root

    def read_config(self) -> dict:
        return read_config()

    def refresh(self):
        self.refresh_signal.emit()

    def get_list_of_paths(self, directory: str) -> list:
        '''
        retrieves a list of files and folders given a directory path
        '''

    def perform_task(self, task: ExplorerTask) -> MyThread:
        '''
        performs a given action using multithreading
        '''

    def status_update(func):
        def inner(self, task: ExplorerTask):
            task.status = TaskItemStatus.RUNNING
            task.emit_update()

            func(self, task)

            task.status = TaskItemStatus.DONE
            task.emit_update()

        return inner

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