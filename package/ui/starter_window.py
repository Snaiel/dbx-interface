from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFormLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt

INFO_TEXT = '''
1. Select a 'Scoped access' API
2. Choose 'Full Dropbox' access type
3. Name the app
        for example: dbx-interface-8927612423
        (name must be original, thus numbers)
4. Create app
5. Go to 'Permissions' tab
5. Tick the following boxes:
        • files.metadata.write
        • files.metadata.read
        • files.content.write
        • files.content.read
6. Click 'Submit'
7. Go back to 'Settings' tab
8. Get the 'App key' & 'App secret'
'''

class StarterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Getting Started")

        layout = QGridLayout(self)
        layout.addWidget(InfoBox(), 0, 0)
        layout.addWidget(InputForm(), 0, 1)

        self.setMaximumSize(self.size())

class InfoBox(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(QLabel("Welcome to dbx-interface. To get started,"))
        layout.addWidget(QLabel("click the link below and create an app"))

        link = "https://www.dropbox.com/lp/developers"
        hyperlink = QLabel(f"<a href=\"{link}\">{link}</a>")
        hyperlink.setOpenExternalLinks(True)
        layout.addWidget(hyperlink)

        layout.addWidget(QLabel(INFO_TEXT))

class InputForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(80, 11, 11, 11)

        layout.addWidget(QLabel("App key"))
        self.app_key = QLineEdit(self)
        layout.addWidget(self.app_key)
        layout.addWidget(QLabel("App secret"))
        self.app_secret = QLineEdit(self)
        layout.addWidget(self.app_secret)
