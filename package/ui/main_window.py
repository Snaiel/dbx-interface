from package.dbx_utils import get_list_of_paths
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QDockWidget, QListWidget, QFrame, QScrollArea
from PyQt5.QtSvg import QSvgWidget
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self, dbx):
        super().__init__()
        self.dbx = dbx

        self.dbx_explorer = Explorer(self, dbx)
        self.setCentralWidget(self.dbx_explorer)

        self.dirnames = DirectoryList(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dirnames)

        self.setMinimumWidth(800)

        self._createToolbar()

    def _createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction("Pull")
        self.toolbar.addAction("Push")

    def change_explorer_directory(self, path):
        self.dbx_explorer.show_list_of_items(path)
        self.dbx_explorer.current_directory = path
        self.dirnames.change_displayed_directories(self.dbx_explorer.current_directory)

class DirectoryList(QDockWidget):
    def __init__(self, parent):
        super().__init__('Directories', parent)
        self.setMinimumWidth(200)

        self.list_widget = QListWidget()

        self.list_widget.itemDoubleClicked.connect(lambda object: self.change_path(object))
        self.list_widget.addItem('My Dropbox')

        self.setWidget(self.list_widget)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

    def change_displayed_directories(self, path):
        print(path)
        self.list_widget.clear()
        self.list_widget.addItem('My Dropbox')
        directories = path.split('/')[1:]
        self.list_widget.addItems(directories)

    def change_path(self, object):
        new_path = ''
        if not object.text() == 'My Dropbox':
            for i in range(1, self.list_widget.count()):
                item = self.list_widget.item(i)
                new_path += f'/{item.text()}'
                if item == object:
                    break

        print(new_path)
        self.parentWidget().change_explorer_directory(new_path)

class Explorer(QScrollArea):
    def __init__(self, parent, dbx):
        super().__init__(parent)
        self.dbx = dbx

        self.current_directory = ''

        self.widget = QWidget(self)
        self.setWidget(self.widget)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)

        self.layout = QVBoxLayout(self.widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.show_list_of_items(self.current_directory)

    def eventFilter(self, object, event):
        if isinstance(object, ExplorerItem):
            if event.type() == QEvent.MouseButtonDblClick:
                self.parentWidget().change_explorer_directory(object.path)
                    
        return False

    def show_list_of_items(self, directory):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
             child.widget().deleteLater()

        data = get_list_of_paths(self.dbx, directory)

        for i in data:
            explorer_item = ExplorerItem(**i)
            explorer_item.installEventFilter(self)
            self.layout.addWidget(explorer_item)

class ExplorerItem(QWidget):
    def __init__(self, path, is_file):
        super().__init__()

        self.path = path
        self.basename = path.split('/')[-1]

        self.item_layout = QHBoxLayout(self)
        self.item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.item_layout.setContentsMargins(0, 2, 0, 2)

        self.checkbox = QCheckBox()

        
        self.icon = QSvgWidget(str(Path(Path(__file__).parent, 'icons', f"{'file-earmark' if is_file else 'folder'}.svg")))
        self.icon.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        self.icon.setMinimumWidth(30)

        self.label = QLabel(self.basename)

        self.item_layout.addWidget(self.checkbox)
        self.item_layout.addWidget(self.icon)
        self.item_layout.addWidget(self.label)