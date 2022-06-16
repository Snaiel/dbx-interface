from package.ui.mainwidgets.dbx_explorer import DropboxExplorer
from package.ui.mainwidgets.local_explorer import LocalExplorer
from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout

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
        central_layout.addWidget(self.dbx_explorer, 0, 0)

        self.local_model = LocalModel()
        self.local_explorer = LocalExplorer(central_widget, self.local_model, local_root)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)

        central_layout.setColumnStretch(0, 1)
        central_layout.setColumnStretch(1, 1)

        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")