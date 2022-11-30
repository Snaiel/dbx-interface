from PyQt5.QtWidgets import QWidget, QListWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QLabel, QMenu, QSplitter, QInputDialog, QApplication, QShortcut
from PyQt5.QtCore import Qt, QEvent, QPoint, QRect, pyqtSlot, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QMouseEvent, QPixmap, QPainter, QBrush, QColor, QCursor, QResizeEvent
from PyQt5.QtSvg import QSvgWidget
from pathlib import Path
from package.model.interface_model import InterfaceModel, ExplorerAction
from package.ui.widgets.task_status import TaskStatusPopup

class Explorer(QSplitter):
    '''
    Widget that allows the navigation of a contained directory structure
    '''

    selection_num_changed = pyqtSignal(QObject, int)
    left_clicked = pyqtSignal(QWidget)

    def __init__(self, parent, model: InterfaceModel, action_status_popup: TaskStatusPopup, current_directory: str):
        super().__init__(parent)
        self.model = model
        self.action_status_popup = action_status_popup
        self.current_directory = current_directory
        self.setChildrenCollapsible(False)

        self.directory_panel : Explorer.DirectoryPanel
        self.item_list : Explorer.ItemList

    def change_explorer_directory(self, path):
        self.current_directory = path
        self.item_list.show_list_of_items(path)
        self.item_list.current_directory = path
        self.directory_panel.change_displayed_directories(self.current_directory)

        self.item_list.selected_items.clear()
        self.selection_num_changed.emit(self, 0)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.left_clicked.emit(self)

    def perform_action(self, action: str, **kwargs):
        ui_action = self.action_status_popup.add_action(kwargs['description'])
        model_action = ExplorerAction(action, **kwargs)
        self.model.perform_action(action, **kwargs)

    class DirectoryPanel(QWidget):
        '''
        A panel that lists all parent directories for easy navigation
        '''

        left_clicked = pyqtSignal(QWidget)

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
            layout.addWidget(self.list_widget)

        def change_displayed_directories(self, path):
            '''
            override for behaviour when changing directories
            '''

        def change_path(self, object):
            '''
            override to change path when a list item is double clicked
            '''

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            self.left_clicked.emit(self)

    class ItemList(QScrollArea):
        '''
        Widget that shows all the files and folders in a given directory
        '''

        left_clicked = pyqtSignal(QWidget)
        selection_num_changed = pyqtSignal(int)

        def __init__(self, parent, model, current_directory):
            super().__init__(parent)

            self.explorer = parent
            self.model = model #type: InterfaceModel
            self.current_directory = current_directory

            self.selected_items = []

            # right click menu
            self.menu = QMenu(self)
            self.menu.addAction("Refresh")
            self.menu.addAction("Open Folder")
            self.menu.installEventFilter(self)

            self.background_widget = Explorer.ItemList.RectangleSelectionBackground(self)
            self.background_widget.right_clicked.connect(self.right_clicked)
            self.background_widget.rectangle_select.connect(self.rectangle_selection)
            self.background_widget.left_clicked.connect(lambda: self.left_clicked.emit(self))
            self.setWidget(self.background_widget)

            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setFrameShape(QFrame.Shape.NoFrame)
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
                explorer_item.selection_state_changed.connect(self.item_selection_state_changed)
                self.list_layout.addWidget(explorer_item)

        def get_explorer_item(self, item_data: list):
            '''
            override to return an explorer item
            '''
            return Explorer.ExplorerItem(self, self.explorer, self.model, item_data[0], item_data[1])

        @pyqtSlot(QMouseEvent)
        def right_clicked(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.RightButton:
                self.menu.popup(QCursor.pos())

        def eventFilter(self, object, event):
            # Item Events
            if isinstance(object, Explorer.ExplorerItem):
                object: Explorer.ExplorerItem
                # Double Clicking an item
                if event.type() == QEvent.Type.MouseButtonDblClick and object.is_file == False:
                    self.parentWidget().change_explorer_directory(object.path)
                elif event.type() == QEvent.Type.Wheel:
                    self.wheelEvent(event)
                elif event.type() == QEvent.Type.MouseButtonRelease:
                    self.left_clicked.emit(self)
            elif object == self.menu and event.type() == QEvent.Type.MouseButtonRelease:
                # Right clicking an empty space in the item list
                action = object.actionAt(event.pos()).text()
                print(action)
                self.process_action(action)
                        
            return False

        @pyqtSlot(QRect, bool)
        def rectangle_selection(self, rect: QRect, deselect: bool):
            for i in range(len(self.list_layout)):
                explorer_item = self.list_layout.itemAt(i).widget()
                if rect.intersects(explorer_item.geometry()):
                    explorer_item.select_item(not deselect)

        @pyqtSlot(object)
        def item_selection_state_changed(self, item):
            item: Explorer.ExplorerItem
            if item in self.selected_items:
                self.selected_items.remove(item)
            else:
                self.selected_items.append(item)
            self.selection_num_changed.emit(self.parent(), len(self.selected_items))

        def select_all(self):
            for i in range(len(self.list_layout)):
                explorer_item = self.list_layout.itemAt(i).widget()
                explorer_item.select_item()

        def deselect_all(self):
            for i in range(len(self.list_layout)):
                explorer_item = self.list_layout.itemAt(i).widget()
                explorer_item.select_item(False)

        def process_action(self, action: str) -> None:
            if action == 'Refresh':
                self.show_list_of_items(self.current_directory)
            elif action == 'Open Folder':
                self.model.open_path(self.current_directory)

        class RectangleSelectionBackground(QWidget):

            left_clicked = pyqtSignal()
            right_clicked = pyqtSignal(QMouseEvent)
            rectangle_select = pyqtSignal(QRect, bool)

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

            def mouseReleaseEvent(self, event: QMouseEvent):
                self.selecting = False
                if event.button() == Qt.MouseButton.LeftButton:
                    modifiers = QApplication.keyboardModifiers()
                    deselect = False
                    if modifiers == Qt.KeyboardModifier.ControlModifier:
                        deselect = True
                    rect = QRect(self.begin, self.destination)
                    self.rectangle_select.emit(rect, deselect)
                    self.left_clicked.emit()
                    painter = QPainter(self.pix)
                    painter.fillRect(rect.normalized(), QBrush(Qt.GlobalColor.transparent))
                elif event.button() == Qt.MouseButton.RightButton:
                    self.right_clicked.emit(event)
                self.update()

    class ExplorerItem(QWidget):
        selection_state_changed = pyqtSignal(object)

        def __init__(self, parent, explorer, model, path, is_file):
            super().__init__(parent)

            self.explorer = explorer
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
            
            self.icon = QSvgWidget(str(Path(Path(__file__).parents[2], 'icons', f"{'file-earmark' if is_file else 'folder'}.svg")))
            self.icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
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
            self.select_item(True if self.checkbox.isChecked() else False)
            self.selection_state_changed.emit(self)

        def select_item(self, selected = True):
            self.checkbox.setChecked(selected)
            if selected:
                self.setStyleSheet("background-color: #D2D2D2;")
            else:
                self.setStyleSheet("QWidget::hover"
                            "{"
                            "   background-color: #D2D2D2;"
                            "}")

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
                    description = f"Rename {self.path} to {new_path}"
                    self.explorer.perform_action('move', path=self.path, new_path=new_path, description=description)
                    self.path = new_path
                    self.basename = text
            elif action == "Delete":
                description = f"Delete {self.path}"
                self.explorer.perform_action('delete', path=self.path, description=description)
                self.deleteLater()
            elif action == 'Open':
                description = f"Open {self.path}"
                self.explorer.perform_action('open', path=self.path, description=description)
            elif action == 'Open Containing Folder':
                parent = self
                while not isinstance(parent, Explorer.ItemList):
                    parent = parent.parentWidget()
                description = f"Open {parent.current_directory}"
                self.explorer.perform_action('open', path=parent.current_directory, description=description)