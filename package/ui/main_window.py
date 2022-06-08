from package.ui.mainwidgets.dbx_explorer import DropboxExplorer
from package.ui.mainwidgets.local_explorer import LocalExplorer
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, dbx, local_root):
        super().__init__()
        self.dbx = dbx

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self.dbx_explorer = DropboxExplorer(central_widget, dbx)
        central_layout.addWidget(self.dbx_explorer, 0, 0)

        self.local_explorer = LocalExplorer(central_widget, dbx, local_root)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)

        central_layout.setColumnStretch(0, 1)
        central_layout.setColumnStretch(1, 1)

        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")