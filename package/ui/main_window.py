from package.model.interface_model import InterfaceModel
from package.ui.widgets.dbx_explorer import DropboxExplorer
from package.ui.widgets.explorer import Explorer
from package.ui.widgets.local_explorer import LocalExplorer
from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QShortcut, QStatusBar, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QKeySequence

class MainWindow(QMainWindow):
    def __init__(self, dbx, local_root):
        super().__init__()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        # Status Bar
        self.status_bar = MainWindow.StatusBar()
        self.setStatusBar(self.status_bar)

        # Dropbox Interface
        self.dbx_model = DropboxModel(dbx)
        self.dbx_model.action_update.connect(self.status_bar.update_action_status)

        self.dbx_explorer = DropboxExplorer(central_widget, self.dbx_model)
        self.dbx_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        central_layout.addWidget(self.dbx_explorer, 0, 0)
        self.dbx_explorer.left_clicked.connect(self.explorer_focus)

        # Local Interface
        self.local_model = LocalModel()
        self.local_model.action_update.connect(self.status_bar.update_action_status)

        self.local_explorer = LocalExplorer(central_widget, self.local_model, local_root)
        self.local_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)
        self.local_explorer.left_clicked.connect(self.explorer_focus)

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

    class StatusBar(QStatusBar):
        def __init__(self):
            super().__init__()

            self.showMessage("")

            self.cloud = MainWindow.StatusBar.StatusBarSection()
            self.local = MainWindow.StatusBar.StatusBarSection()

            self.addWidget(self.cloud, 21)
            self.addWidget(self.local, 20)

        @pyqtSlot(QObject, int)
        def update_num_selected(self, explorer: QObject, num: int):
            statusbar_section = self._get_statusbar_section(explorer) # type: MainWindow.StatusBar.StatusBarSection
            statusbar_section.set_num_selected(num)

        @pyqtSlot(QObject, str)
        def update_action_status(self, model: QObject, message: str):
            statusbar_section = self._get_statusbar_section(model) # type: MainWindow.StatusBar.StatusBarSection
            statusbar_section.set_action_status(message)

        def _get_statusbar_section(self, origin: QObject):
            statusbar_section = None
            if isinstance(origin, DropboxExplorer) or isinstance(origin, DropboxModel):
                statusbar_section = self.cloud
            elif isinstance(origin, LocalExplorer) or isinstance(origin, LocalModel):
                statusbar_section = self.local
            return statusbar_section

        class StatusBarSection(QWidget):
            def __init__(self):
                super().__init__()

                self.section_layout = QHBoxLayout()
                self.section_layout.setContentsMargins(0, 0, 0, 0)
                self.setLayout(self.section_layout)
                
                self.num_selected = QLabel("0 items selected")
                self.action_status = QLabel("no actions performed")

                self.section_layout.addWidget(self.num_selected)
                self.section_layout.addWidget(self.action_status)

            def set_num_selected(self, num: int):
                self.num_selected.setText(f"{num} items selected")

            def set_action_status(self, message: str):
                self.action_status.setText(message)