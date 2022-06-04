from PyQt5.QtWidgets import QWidget, QListWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QLabel, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtSvg import QSvgWidget
from package.dbx_utils import get_list_of_paths
from pathlib import Path

class Explorer(QSplitter):
    def __init__(self, parent, dbx):
        super().__init__(parent)

        self.dbx = dbx
        self.current_directory = ""

        self.setContentsMargins(0, 0, 0, 0)
        self.directory_panel = DirectoryPanel(self)
        self.item_list = ItemList(self, dbx, self.current_directory)

        self.setChildrenCollapsible(False)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

        self.addWidget(self.directory_panel)
        self.addWidget(self.item_list)

    def change_explorer_directory(self, path):
        self.current_directory = path
        self.item_list.show_list_of_items(path)
        self.item_list.current_directory = path
        self.directory_panel.change_displayed_directories(self.current_directory)

class DirectoryPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Dropbox")
        header.setStyleSheet("padding: 8px, 0px; font-weight: 500")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda object: self.change_path(object))
        self.list_widget.addItem("My Dropbox")
        layout.addWidget(self.list_widget)

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

class ItemList(QScrollArea):
    def __init__(self, parent, dbx, current_directory):
        super().__init__(parent)
        self.dbx = dbx
        self.current_directory = current_directory

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