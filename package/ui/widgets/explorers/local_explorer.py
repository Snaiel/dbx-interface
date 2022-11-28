from PyQt5.QtWidgets import QWidget
from package.ui.widgets.explorers import explorer

class LocalExplorer(explorer.Explorer):
    def __init__(self, parent, model, root: str):
        super().__init__(parent, model, root)
        
        self.directory_panel = self.LocalDirectoryPanel(self, root, "Local Dropbox")
        self.item_list = self.LocalItemList(self, model, self.current_directory)

        self.item_list.selection_num_changed.connect(lambda num: self.selection_num_changed.emit(self, num))

        self.directory_panel.left_clicked.connect(self.mouseReleaseEvent)
        self.item_list.left_clicked.connect(self.mouseReleaseEvent)

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
        def __init__(self, parent, model, current_directory):
            super().__init__(parent, model, current_directory)

        def get_explorer_item(self, item_data: list):
            return LocalExplorer.LocalExplorerItem(self, self.model, item_data[0], item_data[1])

    class LocalExplorerItem(explorer.Explorer.ExplorerItem):
        def __init__(self, parent, model,  path, is_file):
            super().__init__(parent, model,  path, is_file)
