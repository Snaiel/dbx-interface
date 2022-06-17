from posixpath import basename
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import QEvent
from package.model.dbx_model import DropboxModel
from package.ui.mainwidgets import explorer
from pathlib import Path

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

        def get_explorer_item(self, item_data: list):
            return DropboxExplorer.DropboxExplorerItem(self, self.model, item_data[0], item_data[1])

    class DropboxExplorerItem(explorer.Explorer.ExplorerItem):
        def __init__(self, parent, model,  path, is_file):
            super().__init__(parent, model,  path, is_file)
            self.model = model # type: DropboxModel

        def create_right_click_menu(self):
            super().create_right_click_menu()
            self.menu.addSeparator()
            self.menu.addAction("Download")

        def eventFilter(self, object, event: QEvent) -> bool:
            return super().eventFilter(object, event)

        def process_action(self, action: str) -> None:
            super().process_action(action)
            if action == 'Download':
                download_path = QFileDialog.getSaveFileName(self, "Download Location", str(Path.home())+f"/Downloads/{self.basename}")[0]
                self.model.download(self.path, download_path)
                