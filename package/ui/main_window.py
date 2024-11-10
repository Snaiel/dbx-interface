from os.path import dirname, join, realpath
from sys import argv

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QGridLayout, QMainWindow, QShortcut, QWidget

from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from package.ui.widgets.explorers.dbx_explorer import DropboxExplorer
from package.ui.widgets.explorers.local_explorer import LocalExplorer
from package.ui.widgets.statusbar import StatusBar
from package.ui.widgets.task_status import TaskStatusPopup


class MainWindow(QMainWindow):
    def __init__(self, dbx, local_root):
        super().__init__()
        self.setWindowTitle("dbx-interface")
        self.setWindowIcon(QIcon(join(dirname(realpath(argv[0])), "icon.png")))

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Action Status Popups
        self.dbx_tasks_status = TaskStatusPopup(self)
        self.status_bar.cloud.tasks_label_clicked.connect(self.dbx_tasks_status.toggle)
        self.local_tasks_status = TaskStatusPopup(self)
        self.status_bar.local.tasks_label_clicked.connect(self.local_tasks_status.toggle)

        # Dropbox Interface
        self.dbx_model = DropboxModel(local_root, dbx)
        self.dbx_model.refresh_signal.connect(self.refresh)
        
        self.dbx_explorer = DropboxExplorer(central_widget, self.dbx_model, self.dbx_tasks_status)
        self.dbx_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        self.dbx_explorer.task_status_changed.connect(self.status_bar.update_task_status)
        central_layout.addWidget(self.dbx_explorer, 0, 0)
        self.dbx_explorer.left_clicked.connect(self.explorer_focus)

        # Local Interface
        self.local_model = LocalModel(local_root, self.dbx_model)
        self.local_model.refresh_signal.connect(self.refresh)

        self.local_explorer = LocalExplorer(central_widget, self.local_model, self.local_tasks_status, local_root)
        self.local_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        self.local_explorer.task_status_changed.connect(self.status_bar.update_task_status)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)
        self.local_explorer.left_clicked.connect(self.explorer_focus)

        self.dbx_tasks_status.set_explorer(self.dbx_explorer)
        self.local_tasks_status.set_explorer(self.local_explorer)

        # Set the initial focused explorer
        self.focused_explorer = self.dbx_explorer

        central_layout.setColumnStretch(0, 1)
        central_layout.setColumnStretch(1, 1)

        self._create_shortcuts()

    def _create_shortcuts(self):
        select_all = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        select_all.activated.connect(lambda: self.focused_explorer.item_list.select_all())

        deselect_all = QShortcut(QKeySequence("Ctrl+D"), self)
        deselect_all.activated.connect(lambda: self.focused_explorer.item_list.deselect_all())

    @pyqtSlot(QWidget)
    def explorer_focus(self, widget: QWidget):
        self.focused_explorer = widget

    @pyqtSlot()
    def refresh(self):
        self.dbx_explorer.refresh_explorer()
        self.local_explorer.refresh_explorer()