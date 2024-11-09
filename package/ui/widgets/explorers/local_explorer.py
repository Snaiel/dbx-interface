from PyQt5.QtWidgets import QWidget, QMenu,QMessageBox
from package.ui.widgets.explorers.base.explorer import Explorer
from package.ui.widgets.explorers.base.directory_panel import DirectoryPanel
from package.ui.widgets.explorers.base.item_list import ItemList
from package.ui.widgets.explorers.base.explorer_item import ExplorerItem

class LocalExplorer(Explorer):
    def __init__(self, parent, model, action_status_popup, root: str):
        super().__init__(parent, model, action_status_popup, root)
        
        self.directory_panel = self.LocalDirectoryPanel(self, root, "Local Dropbox")
        self.item_list = self.LocalItemList(self, model, self.current_directory)

        self.item_list.selection_num_changed.connect(lambda num: self.selection_num_changed.emit(self, num))

        self.directory_panel.left_clicked.connect(self.mouseReleaseEvent)
        self.item_list.left_clicked.connect(self.mouseReleaseEvent)
        self.item_list.perform_task.connect(self.process_task)

        self.addWidget(self.directory_panel)
        self.addWidget(self.item_list)

        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

    class LocalDirectoryPanel(DirectoryPanel):
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

    class LocalItemList(ItemList):
        def __init__(self, parent, model, current_directory):
            super().__init__(parent, model, current_directory)

        def get_explorer_item(self, item_data: list):
            return LocalExplorer.LocalExplorerItem(self, self.explorer, self.model, item_data[0], item_data[1])
        
        def create_right_click_menu(self):
            super().create_right_click_menu()
            self.menu.addSeparator()
            self.menu.addAction("Sync")

        def process_action(self, action: str) -> None:
            super().process_action(action)
            if action == 'Sync':
                self.perform_task.emit('sync', {'description': 'Syncing local files'})

    class LocalExplorerItem(ExplorerItem):
        def __init__(self, parent, explorer, model,  path, is_file):
            super().__init__(parent, explorer, model,  path, is_file)

        def create_right_click_menu(self):
            self.menu = QMenu(self)
            self.menu.addAction("Rename")
            self.menu.addSection("Delete")
            self.menu.addAction("Local Only")
            self.menu.addAction("Local and Cloud")
            self.menu.addSeparator()
            self.menu.addAction("Open")
            self.menu.addAction("Open Containing Folder")
            self.menu.addSeparator()
            self.menu.addAction("Mark as Synced")

        def process_action(self, action: str) -> None:
            super().process_action(action)
            if action == "Local Only":
                msg = QMessageBox(self)
                msg.setText(f"Are you sure you want to delete \"{self.basename}\" locally?")
                msg.setInformativeText("This cannot be undone.")
                msg.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes)
                msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
                answer = msg.exec()
                if answer == QMessageBox.StandardButton.Yes:
                    description = f"Delete \"{self.path}\""
                    self.perform_task.emit('delete_local', {"path":self.path, "description":description})
                    self.deleteLater()
            elif action == "Local and Cloud":
                msg = QMessageBox(self)
                msg.setText(f"Are you sure you want to delete \"{self.basename}\" both locally and in the cloud?")
                msg.setInformativeText("This cannot be undone.")
                msg.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes)
                msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
                answer = msg.exec()
                if answer == QMessageBox.StandardButton.Yes:
                    description = f"Delete \"{self.path}\""
                    self.perform_task.emit('delete_local_and_cloud', {"path":self.path, "description":description})
                    self.deleteLater()
            elif action == "Mark as Synced":
                description = f"Mark \"{self.path}\" as Synced"
                self.perform_task.emit('mark_as_synced', {"path":self.path, "description":description, "is_file":self.is_file})
