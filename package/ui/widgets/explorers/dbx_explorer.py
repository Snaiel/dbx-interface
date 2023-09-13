from pathlib import Path
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QAction
from PyQt5.QtCore import QEvent
from package.ui.widgets.explorers.base.explorer import Explorer
from package.ui.widgets.explorers.base.directory_panel import DirectoryPanel
from package.ui.widgets.explorers.base.item_list import ItemList
from package.ui.widgets.explorers.base.explorer_item import ExplorerItem

class DropboxExplorer(Explorer):
    def __init__(self, parent, model, action_status_popup):
        super().__init__(parent, model, action_status_popup, "")
        
        self.directory_panel = self.DropboxDirectoryPanel(self, "", "Dropbox Cloud")
        self.item_list = self.DropboxItemList(self, model, self.current_directory)

        self.item_list.selection_num_changed.connect(lambda num: self.selection_num_changed.emit(self, num))

        self.directory_panel.left_clicked.connect(self.mouseReleaseEvent)
        self.item_list.left_clicked.connect(self.mouseReleaseEvent)
        self.item_list.perform_task.connect(self.process_task)

        self.addWidget(self.directory_panel)
        self.addWidget(self.item_list)

        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

    class DropboxDirectoryPanel(DirectoryPanel):
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

    class DropboxItemList(ItemList):
        def __init__(self, parent, model, current_directory):
            super().__init__(parent, model, current_directory)

        def get_explorer_item(self, item_data: list):
            return DropboxExplorer.DropboxExplorerItem(self, self.explorer, self.model, item_data[0], item_data[1])
        
        def create_right_click_menu(self):
            super().create_right_click_menu()
            self.menu.addSeparator()
            self.menu.addAction("Upload file")
            self.menu.addAction("Upload folder")

        def process_action(self, action: str) -> None:
            super().process_action(action)
            if action == 'Upload file':
                file_path = QFileDialog.getOpenFileName(self, "Select File to Upload", str(Path.home()))[0]
                dbx_path = self.current_directory + f"/{Path(file_path).name}"
                description = f"Upload \"{file_path}\" to \"{self.current_directory}\""
                self.perform_task.emit('upload_file', {"path":file_path, "dbx_path":dbx_path, "description":description})
            elif action == 'Upload folder':
                folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Upload", str(Path.home()))
                dbx_path = self.current_directory + f"/{Path(folder_path).name}"
                description = f"Upload \"{folder_path}\" to \"{self.current_directory}\""
                self.perform_task.emit('upload_folder', {"path":folder_path, "dbx_path":dbx_path, "description":description})

    class DropboxExplorerItem(ExplorerItem):
        def __init__(self, parent, explorer, model,  path, is_file):
            super().__init__(parent, explorer, model,  path, is_file)

        def create_right_click_menu(self):
            super().create_right_click_menu()
            self.menu.addSeparator()
            self.menu.addAction("Download")
            self.menu.addAction("Sync")

        def eventFilter(self, object, event: QEvent) -> bool:
            return super().eventFilter(object, event)

        def process_action(self, action: str) -> None:
            super().process_action(action)
            if action == 'Download':
                dialog_path = str(Path.home())+f"/Downloads/{self.basename}"
                dialog_path += "" if self.is_file else ".zip"
                result = QFileDialog.getSaveFileName(self, "Download Location", dialog_path)
                download_path = result[0]
                if download_path:
                    description = f"Download \"{self.path}\" to \"{download_path}\""
                    self.perform_task.emit('download', {"path":self.path, "local_path":download_path, "description":description})
            elif action == 'Sync':
                self.perform_task.emit('sync', {"local_path":self.model.read_config()["DROPBOX_LOCATION"], "dbx_path":self.path, "description": "Syncing to local"})