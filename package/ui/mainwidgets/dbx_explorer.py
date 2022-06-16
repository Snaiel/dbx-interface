from PyQt5.QtWidgets import QWidget
from package.ui.mainwidgets import explorer

class DropboxExplorer(explorer.Explorer):
    def __init__(self, parent, model):
        super().__init__(parent, model, "")
        
        self.directory_panel = self.DropboxDirectoryPanel(self, "", "Dropbox Cloud")
        self.item_list = self.DropboxItemList(self, model, self.current_directory)

        self.addWidget(self.directory_panel)
        self.addWidget(self.item_list)

        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

    class DropboxDirectoryPanel(explorer.Explorer.DirectoryPanel):
        def __init__(self, parent: QWidget, current_directory: str, header: str):
            super().__init__(parent, current_directory, header)
            self.list_widget.addItem("My Dropbox")

        def change_displayed_directories(self, path):
            self.current_directory = path
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

            self.change_displayed_directories(new_path)
            self.parentWidget().change_explorer_directory(new_path)

    class DropboxItemList(explorer.Explorer.ItemList):
        def __init__(self, parent, model, current_directory):
            super().__init__(parent, model, current_directory)
            self.show_list_of_items(self.current_directory)