from pathlib import Path
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QMenu, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from package.model.interface_model import InterfaceModel

class ExplorerItem(QWidget):

    selection_state_changed = pyqtSignal(object)
    perform_task = pyqtSignal(str, dict)

    def __init__(self, parent, explorer, model, path, is_file):
        super().__init__(parent)

        self.item_list = parent
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
        
        self.icon = QSvgWidget(str(Path(Path(__file__).parents[3], 'icons', f"{'file-earmark' if is_file else 'folder'}.svg")))
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
                self.setStyleSheet("QWidget::hover"
                        "{"
                        "   background-color: #D2D2D2;"
                        "}")
                new_path = self.path.split("/")
                new_path = new_path[:-1]
                new_path.append(text)
                new_path = "/".join(new_path)
                description = f"Rename \"{self.path}\" to \"{new_path}\""
                self.perform_task.emit('rename', {"path":self.path, "new_path":new_path, "description":description})
                self.path = new_path
                self.basename = text
        elif action == "Delete":
            msg = QMessageBox(self)
            msg.setText(f"Are you sure you want to delete \"{self.basename}\"?")
            msg.setInformativeText("This cannot be undone.")
            msg.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes)
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            answer = msg.exec()
            if answer == QMessageBox.StandardButton.Yes:
                description = f"Delete \"{self.path}\""
                self.perform_task.emit('delete', {"path":self.path, "description":description})
                self.deleteLater()
        elif action == 'Open':
            description = f"Open \"{self.path}\""
            self.perform_task.emit('open', path=self.path, description=description)
        elif action == 'Open Containing Folder':
            parent = self.item_list
            description = f"Open \"{parent.current_directory}\""
            self.perform_task.emit('open', {"path":parent.current_directory, "description":description})