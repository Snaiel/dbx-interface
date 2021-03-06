from PyQt5.QtWidgets import QWidget, QListWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QLabel, QMenu, QSplitter, QInputDialog
from PyQt5.QtCore import Qt, QEvent, QPoint, QRect
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QMouseEvent, QPixmap, QPainter, QBrush, QColor

from pathlib import Path
from package.model.interface_model import InterfaceModel

class Explorer(QSplitter):
    '''
    Widget that allows the navigation of a contained directory structure
    '''
    def __init__(self, parent, model, current_directory):
        super().__init__(parent)
        self.model = model # type: InterfaceModel
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
        def __init__(self, parent, model, current_directory):
            super().__init__(parent)

            self.model = model #type: InterfaceModel
            self.current_directory = current_directory

            self.selected_items = []

            # right click menu
            self.menu = QMenu(self)
            self.menu.addAction("Refresh")
            self.menu.addAction("Open Folder")
            self.menu.installEventFilter(self)

            self.background_widget = Explorer.ItemList.RectangleSelectionBackground(self)
            self.setWidget(self.background_widget)

            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setFrameShape(QFrame.NoFrame)
            self.setWidgetResizable(True)

            self.list_layout = QVBoxLayout(self.background_widget)
            self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            self.list_layout.setContentsMargins(4, 16, 20, 16)

            self.show_list_of_items(self.current_directory)

        def show_list_of_items(self, directory):
            while self.list_layout.count():
                child = self.list_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            data = self.model.get_list_of_paths(directory)

            for i in data:
                explorer_item = self.get_explorer_item(i)
                explorer_item.installEventFilter(self)
                self.list_layout.addWidget(explorer_item)

        def get_explorer_item(self, item_data: list):
            '''
            override to return an explorer item
            '''
            return Explorer.ExplorerItem(self, self.model, item_data[0], item_data[1])

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            if event.button() == Qt.MouseButton.RightButton:
                self.menu.popup(event.globalPos())

        def eventFilter(self, object, event):
            # Item Events
            if isinstance(object, Explorer.ExplorerItem):
                object: Explorer.ExplorerItem
                # Double Clicking an item
                if event.type() == QEvent.Type.MouseButtonDblClick and object.is_file == False:
                    self.parentWidget().change_explorer_directory(object.path)
            # Right clicking an empty space in the item list
            elif object == self.menu and event.type() == QEvent.Type.MouseButtonRelease:
                action = object.actionAt(event.pos()).text()
                print(action)
                self.process_action(action)
                        
            return False

        def rectangle_select(self, rect: QRect):
            for i in range(len(self.list_layout)):
                explorer_item = self.list_layout.itemAt(i).widget()
                if rect.intersects(explorer_item.geometry()):
                    explorer_item.select_item(True)

        def process_action(self, action: str) -> None:
            if action == 'Refresh':
                self.show_list_of_items(self.current_directory)
            elif action == 'Open Folder':
                self.model.open_path(self.current_directory)

        class RectangleSelectionBackground(QWidget):
            def __init__(self, parent):
                super().__init__(parent)

                self.pix = QPixmap(self.rect().size())
                self.pix.fill(Qt.GlobalColor.transparent)

                self.begin, self.destination = QPoint(), QPoint()
                self.selecting = False

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.drawPixmap(QPoint(), self.pix)
                if not self.begin.isNull() and not self.destination.isNull() and self.selecting:
                    rect = QRect(self.begin, self.destination)
                    painter.fillRect(rect.normalized(), QBrush(QColor(210, 210, 210)))

            def mousePressEvent(self, event):
                if event.buttons() == Qt.MouseButton.LeftButton:
                    self.begin = event.pos()
                    self.destination = self.begin
                    self.selecting = True
                    self.update()

            def mouseMoveEvent(self, event):
                if event.buttons() == Qt.MouseButton.LeftButton:
                    self.destination = event.pos()
                    self.update()

            def mouseReleaseEvent(self, event):
                self.selecting = False
                if event.button() == Qt.MouseButton.LeftButton:
                    rect = QRect(self.begin, self.destination)
                    self.parentWidget().parentWidget().rectangle_select(rect)
                    painter = QPainter(self.pix)
                    painter.fillRect(rect.normalized(), QBrush(Qt.GlobalColor.transparent))
                self.update()

    class ExplorerItem(QWidget):
        def __init__(self, parent, model, path, is_file):
            super().__init__(parent)

            self.model = model #type: InterfaceModel
            self.path = path
            self.basename = path.split('/')[-1]

            self.is_file = is_file

            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

            self.setStyleSheet("QWidget::hover"
                            "{"
                            "background-color: #D2D2D2;"
                            "}")

            self.item_layout = QHBoxLayout(self)
            self.item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.item_layout.setContentsMargins(8, 4, 8, 4)

            self.checkbox = QCheckBox()
            self.checkbox.stateChanged.connect(self.checkbox_clicked)
            
            self.icon = QSvgWidget(str(Path(Path(__file__).parent, 'icons', f"{'file-earmark' if is_file else 'folder'}.svg")))
            self.icon.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            self.icon.setMinimumWidth(30)

            self.label = QLabel(self.basename)

            self.item_layout.addWidget(self.checkbox)
            self.item_layout.addWidget(self.icon)
            self.item_layout.addWidget(self.label)

            self.create_right_click_menu()

            self.menu.installEventFilter(self)

        def create_right_click_menu(self):
            self.menu = QMenu(self)
            self.menu.addAction("Rename")
            self.menu.addAction("Delete")
            self.menu.addSeparator()
            self.menu.addAction("Open")
            self.menu.addAction("Open Containing Folder")

        def checkbox_clicked(self):
            self.select_item(True if self.checkbox.isChecked() else False )

        def select_item(self, selected):
            parent = self.parentWidget().parentWidget().parentWidget()
            self.checkbox.setChecked(selected)
            if selected:
                self.setStyleSheet("background-color: #D2D2D2;")
                if self not in parent.selected_items:
                    parent.selected_items.append(self)
            else:
                self.setStyleSheet("QWidget::hover"
                            "{"
                            "background-color: #D2D2D2;"
                            "}")
                parent.selected_items.remove(self)

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            if event.button() == Qt.MouseButton.RightButton:
                self.menu.popup(event.globalPos())
        
        def eventFilter(self, object, event:QEvent) -> bool:
            if object == self.menu and event.type() == QEvent.Type.MouseButtonRelease:
                action = object.actionAt(event.pos()).text()
                print(action)
                self.process_action(action)
            return False

        def process_action(self, action: str) -> None:
            if action == 'Rename':
                text, ok = QInputDialog.getText(self, "Rename", "What do you want to rename to?", text=self.basename)
                if ok and text:
                    self.label.setText(text)
                    new_path = self.path.split("/")
                    new_path = new_path[:-1]
                    new_path.append(text)
                    new_path = "/".join(new_path)
                    self.model.move(self.path, new_path)

                    self.path = new_path
                    self.basename = text
            elif action == "Delete":
                self.model.delete(self.path)
                self.deleteLater()
            elif action == 'Open':
                self.model.open_path(self.path)
            elif action == 'Open Containing Folder':
                parent = self
                while not isinstance(parent, Explorer.ItemList):
                    parent = parent.parentWidget()
                self.model.open_path(parent.current_directory)