from package.ui.widgets.explorers.dbx_explorer import DropboxExplorer
from package.ui.widgets.explorers.local_explorer import LocalExplorer
from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from package.model.interface_model import ExplorerTask, TaskItemStatus
from PyQt5.QtWidgets import QWidget, QLabel, QStatusBar, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QEvent, Qt
from PyQt5.QtGui import QResizeEvent

class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()

        self.showMessage("")

        self.cloud = StatusBar.StatusBarSection()
        self.local = StatusBar.StatusBarSection()

        self.addWidget(self.cloud, 21)
        self.addWidget(self.local, 20)

    @pyqtSlot(QObject, int)
    def update_num_selected(self, explorer: QObject, num: int):
        statusbar_section = self._get_statusbar_section(explorer) # type: StatusBar.StatusBarSection
        statusbar_section.set_num_selected(num)

    @pyqtSlot(QObject, ExplorerTask)
    def update_task_status(self, model: QObject, task: ExplorerTask):
        statusbar_section = self._get_statusbar_section(model) # type: StatusBar.StatusBarSection
        if task.status == TaskItemStatus.DONE:
            statusbar_section.set_task_status("no tasks to perform")
        else:
            statusbar_section.set_task_status(task.kwargs["description"])

    def _get_statusbar_section(self, origin: QObject):
        statusbar_section = None
        if isinstance(origin, DropboxExplorer) or isinstance(origin, DropboxModel):
            statusbar_section = self.cloud
        elif isinstance(origin, LocalExplorer) or isinstance(origin, LocalModel):
            statusbar_section = self.local
        return statusbar_section

    class StatusBarSection(QWidget):

        tasks_label_clicked = pyqtSignal()
        
        def __init__(self):
            super().__init__()

            self.section_layout = QHBoxLayout()
            self.section_layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(self.section_layout)
            
            self.num_selected = QLabel("0 items selected")
            self.task_status = QLabel("no tasks to perform")
            self.task_status.setStyleSheet("QWidget::hover"
                        "{"
                        "background-color: #D2D2D2;"
                        "}")

            self.task_status.installEventFilter(self)

            self.section_layout.addWidget(self.num_selected)
            self.section_layout.addWidget(self.task_status)

        def set_num_selected(self, num: int):
            self.num_selected.setText(f"{num} items selected")

        def set_task_status(self, message: str):
            self.task_status.setText(message)

        def eventFilter(self, object: QObject, event: QEvent) -> bool:
            if object == self.task_status and event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self.tasks_label_clicked.emit()
            return False    

        def resizeEvent(self, event: QResizeEvent) -> None:
            self.task_status.setMaximumWidth(int(self.width() * 0.7))
            return super().resizeEvent(event)