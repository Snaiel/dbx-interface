from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

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