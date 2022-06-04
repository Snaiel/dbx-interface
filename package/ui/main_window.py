from package.ui.mainwidgets.explorer import Explorer
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self, dbx):
        super().__init__()
        self.dbx = dbx

        self.dbx_explorer = Explorer(self, dbx)
        self.setCentralWidget(self.dbx_explorer)

        self.setMinimumWidth(800)

        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")