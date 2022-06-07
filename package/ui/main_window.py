from package.ui.mainwidgets.explorer import Explorer
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout
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

        self.dbx_explorer = Explorer(central_widget, dbx)
        central_layout.addWidget(self.dbx_explorer, 0, 0)


        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")