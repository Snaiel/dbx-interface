from package.ui.mainwidgets.dbx_explorer import DropboxExplorer
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, dbx):
        super().__init__()
        self.dbx = dbx

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self.dbx_explorer = DropboxExplorer(central_widget, dbx)
        central_layout.addWidget(self.dbx_explorer, 0, 0)

        self.another = DropboxExplorer(central_widget, dbx)
        central_layout.addWidget(self.another, 0, 1)
        central_layout.setSpacing(0)


        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")