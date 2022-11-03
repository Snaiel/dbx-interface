from package.ui.mainwidgets.dbx_explorer import DropboxExplorer
from package.ui.mainwidgets.local_explorer import LocalExplorer
from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel
from PyQt5.QtCore import pyqtSlot

class MainWindow(QMainWindow):
    def __init__(self, dbx, local_root):
        super().__init__()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self.dbx_model = DropboxModel(dbx)
        self.dbx_explorer = DropboxExplorer(central_widget, self.dbx_model)
        self.dbx_explorer.selection_num_changed.connect(self._update_dbx_cloud_num_selected)
        self.dbx_explorer.item_list.selection_num_changed.connect(self._update_dbx_cloud_num_selected)
        central_layout.addWidget(self.dbx_explorer, 0, 0)

        self.local_model = LocalModel()
        self.local_explorer = LocalExplorer(central_widget, self.local_model, local_root)
        self.local_explorer.selection_num_changed.connect(self._update_dbx_local_num_selected)
        self.local_explorer.item_list.selection_num_changed.connect(self._update_dbx_local_num_selected)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)

        central_layout.setColumnStretch(0, 1)
        central_layout.setColumnStretch(1, 1)

        self._create_tool_bar()
        self._create_status_bar()

    def _create_tool_bar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")

    def _create_status_bar(self):
        self.statusBar().showMessage("")
        self.dbx_cloud = QWidget()
        self.dbx_cloud_num_selected = QLabel(self.dbx_cloud, text="0 items selected")

        self.dbx_local = QWidget()
        self.dbx_local_num_selected = QLabel(self.dbx_local, text="0 items selected")

        self.statusBar().addWidget(self.dbx_cloud, 21)
        self.statusBar().addWidget(self.dbx_local, 20)

    @pyqtSlot(int)
    def _update_dbx_cloud_num_selected(self, num: int):
        self.dbx_cloud_num_selected.setText(f"{num} items selected")

    @pyqtSlot(int)
    def _update_dbx_local_num_selected(self, num: int):
        self.dbx_local_num_selected.setText(f"{num} items selected")