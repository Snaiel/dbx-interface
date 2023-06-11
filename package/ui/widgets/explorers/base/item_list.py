from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QFrame, QMenu, QInputDialog
from PyQt5.QtCore import Qt, QEvent, QRect, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QCursor
from package.ui.widgets.explorers.base.selection_background import RectangleSelectionBackground
from package.ui.widgets.explorers.base.explorer_item import ExplorerItem
from package.model.interface_model import InterfaceModel

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
        self._create_right_click_menu()

        self.background_widget = RectangleSelectionBackground(self)
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

    def _create_right_click_menu(self):
        self.menu = QMenu(self)
        self.menu.addAction("Refresh")
        self.menu.addAction("Create Folder")
        self.menu.addAction("Open Folder")
        self.menu.installEventFilter(self)

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
        return ExplorerItem(self, self.explorer, self.model, item_data[0], item_data[1])

    @pyqtSlot(QMouseEvent)
    def right_clicked(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.menu.popup(QCursor.pos())

    def eventFilter(self, object, event):
        # Item Events
        if isinstance(object, ExplorerItem):
            object: ExplorerItem
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
        item: ExplorerItem
        if item in self.selected_items:
            self.selected_items.remove(item)
        else:
            self.selected_items.append(item)
        self.selection_num_changed.emit(len(self.selected_items))

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
        if action == 'Create Folder':
            text, ok = QInputDialog.getText(self, "Create Folder", "Enter name of new folder:")
            if ok and text:
                path = self.explorer.current_directory.split("/")
                path.append(text)
                path = "/".join(path)
                description = f"Create folder \"{path}\""
                self.explorer.perform_task('create_folder', path=path, description=description)
            self.show_list_of_items(self.current_directory)
        elif action == 'Open Folder':
            description = f"Open \"{self.current_directory}\""
            self.explorer.perform_task('open', path=self.current_directory, description=description)
