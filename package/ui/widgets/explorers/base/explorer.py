from PyQt5.QtWidgets import QWidget, QSplitter
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QMouseEvent
from package.model.interface_model import InterfaceModel, ExplorerTask
from package.ui.widgets.explorers.base.directory_panel import DirectoryPanel
from package.ui.widgets.explorers.base.item_list import ItemList
from package.ui.widgets.task_status import TaskStatusPopup

class Explorer(QSplitter):
    '''
    Widget that allows the navigation of a contained directory structure
    '''

    selection_num_changed = pyqtSignal(QObject, int)
    task_status_changed = pyqtSignal(QObject, str)
    left_clicked = pyqtSignal(QWidget)

    def __init__(self, parent, model: InterfaceModel, action_status_popup: TaskStatusPopup, current_directory: str):
        super().__init__(parent)
        self.model = model
        self.action_status_popup = action_status_popup
        self.current_directory = current_directory
        self.setChildrenCollapsible(False)

        self.directory_panel : DirectoryPanel
        self.item_list : ItemList

    def change_explorer_directory(self, path):
        self.current_directory = path
        self.item_list.show_list_of_items(path)
        self.item_list.current_directory = path
        self.directory_panel.change_displayed_directories(self.current_directory)

        self.item_list.selected_items.clear()
        self.selection_num_changed.emit(self, 0)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.left_clicked.emit(self)

    def perform_task(self, action: str, **kwargs):
        ui_task = self.action_status_popup.add_action(kwargs['description'])
        model_task = ExplorerTask(action, **kwargs)
        model_task.task_update.connect(lambda : ui_task.receive_task_update(model_task))
        model_task.task_update.connect(lambda : self.task_status_changed.emit(self, model_task.kwargs['description']))
        self.model.perform_task(model_task)