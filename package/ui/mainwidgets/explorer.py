from PyQt5.QtWidgets import QWidget, QListWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QLabel, QMenu, QSplitter, QAction
from PyQt5.QtCore import Qt, QEvent, QObject
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QMouseEvent
from pathlib import Path

class Explorer(QSplitter):
    '''
    Widget that allows the navigation of a contained directory structure
    '''
    def __init__(self, parent, current_directory):
        super().__init__(parent)
        self.current_directory = current_directory
        self.setChildrenCollapsible(False)

    def change_explorer_directory(self, path):
        self.current_directory = path
        self.item_list.show_list_of_items(path)
        self.item_list.current_directory = path
        self.directory_panel.change_displayed_directories(self.current_directory)

    class DirectoryPanel(QWidget):
        '''
        A panel that lists all parent directories for easy navigation
        '''
        def __init__(self, parent: QWidget, current_directory: str, header: str):
            super().__init__(parent)
            self.current_directory = current_directory

            self.setMinimumWidth(200)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            header = QLabel(header)
            header.setStyleSheet("padding: 8px, 0px; font-weight: 500")
            layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

            self.list_widget = QListWidget()
            self.list_widget.itemDoubleClicked.connect(lambda object: self.change_path(object))
            # self.list_widget.addItem("My Dropbox")
            layout.addWidget(self.list_widget)

        def change_displayed_directories(self, path):
            '''
            override for behaviour when changing directories
            '''

        def change_path(self, object):
            '''
            override to change path when a list item is double clicked
            '''

    class ItemList(QScrollArea):
        '''
        Widget that shows all the files and folders in a given directory
        '''
        def __init__(self, parent, current_directory):
            super().__init__(parent)
            self.current_directory = current_directory

            # right click menu
            self.menu = QMenu(self)
            self.menu.addAction("Refresh")
            self.menu.addAction("Open Folder")
            self.menu.installEventFilter(self)

            self.widget = QWidget(self)
            self.setWidget(self.widget)

            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setFrameShape(QFrame.NoFrame)
            self.setWidgetResizable(True)

            self.layout = QVBoxLayout(self.widget)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            self.layout.setContentsMargins(4, 16, 20, 16)

        def show_list_of_items(self, directory):
            while self.layout.count():
                child = self.layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            data = self.get_list_of_paths(directory)

            for i in data:
                explorer_item = self.get_explorer_item(i)
                explorer_item.installEventFilter(self)
                self.layout.addWidget(explorer_item)

        def get_list_of_paths(self, directory: str) -> list:
            '''
            override this function to get a list of items in a specficed directory.
            '''

        def get_explorer_item(self, item_data: list):
            '''
            override to return an explorer item
            '''
            return Explorer.ExplorerItem(self, item_data[0], item_data[1])

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            if event.button() == Qt.MouseButton.RightButton:
                self.menu.popup(event.globalPos())

        def eventFilter(self, object, event):
            # Double Clicking an item
            if isinstance(object, Explorer.ExplorerItem):
                if event.type() == QEvent.Type.MouseButtonDblClick and object.is_file == False:
                    self.parentWidget().change_explorer_directory(object.path)
            # Right clicking an empty space in the item list
            elif object == self.menu and event.type() == QEvent.Type.MouseButtonRelease:
                action = object.actionAt(event.pos()).text()
                print(action)
                self.process_action(action)
                        
            return False

        def process_action(self, action: str) -> None:
            '''
            override to handle actions when right clicking an empty spot in the item list
            '''

    class ExplorerItem(QWidget):
        def __init__(self, parent, path, is_file):
            super().__init__(parent)

            self.path = path
            self.basename = path.split('/')[-1]

            self.is_file = is_file

            self.setAttribute(Qt.WA_StyledBackground, True)

            self.setStyleSheet("QWidget::hover"
                            "{"
                            "background-color: #D2D2D2;"
                            "}")

            self.item_layout = QHBoxLayout(self)
            self.item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.item_layout.setContentsMargins(8, 4, 8, 4)

            self.checkbox = QCheckBox()
            
            self.icon = QSvgWidget(str(Path(Path(__file__).parent, 'icons', f"{'file-earmark' if is_file else 'folder'}.svg")))
            self.icon.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            self.icon.setMinimumWidth(30)

            self.label = QLabel(self.basename)

            self.item_layout.addWidget(self.checkbox)
            self.item_layout.addWidget(self.icon)
            self.item_layout.addWidget(self.label)

            # right click menu
            self.menu = QMenu(self)
            self.menu.addAction("Rename")
            self.menu.addAction("Delete")
            self.menu.addSeparator()
            self.menu.addAction("Open")
            self.menu.addAction("Open Containing Folder")

            self.menu.installEventFilter(self)

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            if event.button() == Qt.MouseButton.RightButton:
                self.menu.popup(event.globalPos())