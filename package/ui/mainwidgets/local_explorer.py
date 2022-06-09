from PyQt5.QtWidgets import QWidget, QInputDialog
from PyQt5.QtCore import QEvent
from package.ui.mainwidgets import explorer
import package.utils.local_utils as local_utils

class LocalExplorer(explorer.Explorer):
    def __init__(self, parent, dbx, root: str):
        super().__init__(parent, root)
        self.dbx = dbx
        
        self.directory_panel = self.LocalDirectoryPanel(self, root, "Local Dropbox")
        self.item_list = self.LocalItemList(self, dbx, self.current_directory)

        self.addWidget(self.directory_panel)
        self.addWidget(self.item_list)

        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

    class LocalDirectoryPanel(explorer.Explorer.DirectoryPanel):
        def __init__(self, parent: QWidget, current_directory: str, header: str):
            super().__init__(parent, current_directory, header)

            root_path = current_directory.split("/")
            self.root_directory_index = len(root_path)
            self.base_path = "/".join(root_path[:-1])

            self.list_widget.addItem(root_path[-1])

        def change_displayed_directories(self, path):
            self.current_directory = path
            self.list_widget.clear()
            directories = path.split('/')[self.root_directory_index-1:]
            self.list_widget.addItems(directories)

        def change_path(self, object):
            new_path = self.base_path

            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                new_path += f'/{item.text()}'
                if item == object:
                    break

            self.change_displayed_directories(new_path)
            self.parentWidget().change_explorer_directory(new_path)

    class LocalItemList(explorer.Explorer.ItemList):
        def __init__(self, parent, dbx, current_directory):
            super().__init__(parent, current_directory)
            self.dbx = dbx
            self.show_list_of_items(self.current_directory)

        def show_list_of_items(self, directory):
            while self.layout.count():
                child = self.layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            data = self.get_list_of_paths(directory)

            for i in data:
                explorer_item = LocalExplorer.LocalExplorerItem(self, i[0], i[1])
                explorer_item.installEventFilter(self)
                self.layout.addWidget(explorer_item)

        def get_list_of_paths(self, directory: str) -> list:
            return local_utils.get_list_of_paths(directory)

    class LocalExplorerItem(explorer.Explorer.ExplorerItem):
        def __init__(self, parent, path, is_file):
            super().__init__(parent, path, is_file)

        def eventFilter(self, object, event:QEvent) -> bool:
            if object == self.menu and event.type() == QEvent.Type.MouseButtonRelease:
                action = object.actionAt(event.pos()).text()
                print(action)
                self.process_action(action)
            return False

        def process_action(self, action: str) -> None:
            if action == 'Rename':
                text, ok = QInputDialog.getText(self, "Rename", "What do you want to rename to?")
                if ok and text:
                    self.label.setText(text)
                    local_utils.rename(self.path, text)
            if action == "Delete":
                local_utils.delete(self.path)
                self.deleteLater()
