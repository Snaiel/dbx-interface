from PyQt5.QtWidgets import QWidget, QDialog, QGridLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit
from PyQt5.QtCore import Qt, QEvent, QDir
from package.utils import create_config
import pytz

INFO_TEXT = '''
1. Select the 'Scoped access' API
2. Choose the 'Full Dropbox' access type
3. Name the app
        for example: dbx-interface-8927612423
        (name must be original, thus numbers)
4. Create the app
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

class StarterWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_complete = False

        self.setWindowTitle("Getting Started")

        layout = QGridLayout(self)
        self.dropbox_location = DropboxLocation()
        layout.addWidget(self.dropbox_location, 0, 0, 1, 2)
        layout.addWidget(InfoBox(), 1, 0)
        layout.addWidget(InputForm(self), 1, 1)

        self.setMaximumSize(self.size())

    def eventFilter(self, object, event) -> bool:
        if isinstance(object, QPushButton) and event.type() == QEvent.MouseButtonRelease:
            # print(object.text())
            if object.text() == "Close":
                self.setup_complete = True
                self.close()
            else:
                input_form = object.parent() #type: InputForm
                app_info = input_form.get_app_info()
                create_config(app_info[2], app_info[0], app_info[1], self.dropbox_location.get_location(), app_info[3])
                input_form.set_done_visible()
        return False

class DropboxLocation(QWidget):
    def __init__(self):
        super().__init__()

        layout = QGridLayout(self)
        layout.addWidget(
            QLabel("Welcome to dbx-interface.\nTo get started, provide the desired path location of your local Dropbox folder.\nMake sure to create the Dropbox folder itself."), 
            0, 0, 1, 2
        )
        self.location_line_edit = QLineEdit()
        self.location_picker_button = QPushButton("Select folder")
        self.location_picker_button.setStyleSheet("padding: 3px 25px")
        layout.addWidget(self.location_line_edit, 1, 0)
        layout.addWidget(self.location_picker_button, 1, 1)
        
        self.location_picker_button.clicked.connect(self.pick_location)

    def pick_location(self):
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.Option.ShowDirsOnly
        folder_path = dialog.getExistingDirectory(self, "Select Folder", QDir.homePath())
        self.location_line_edit.setText(folder_path)

    def get_location(self) -> str:
        return self.location_line_edit.text()

class InfoBox(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(QLabel("Next, click the link below and create an app"))

        link = "https://www.dropbox.com/lp/developers"
        hyperlink = QLabel(f"<a href=\"{link}\">{link}</a>")
        hyperlink.setOpenExternalLinks(True)
        layout.addWidget(hyperlink)

        layout.addWidget(QLabel("(Note: if have already set this up on another device,\nyou can just retrieve the info previously created)"))

        layout.addWidget(QLabel(INFO_TEXT))

class InputForm(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 8, 11, 11)

        # App details
        layout.addWidget(QLabel("App key"))
        self.app_key = QLineEdit(self)
        layout.addWidget(self.app_key)
        layout.addWidget(QLabel("App secret"))
        self.app_secret = QLineEdit(self)
        layout.addWidget(self.app_secret)

        self.app_info_submit = QPushButton("Submit")
        self.app_info_submit.setDisabled(True)
        self.app_info_submit.clicked.connect(self.set_auth_visible)
        layout.addWidget(self.app_info_submit)

        self.app_key.textChanged.connect(lambda state, inputs=[self.app_key, self.app_secret], btn=self.app_info_submit:self.toggle_submit_disabled(inputs, btn))
        self.app_secret.textChanged.connect(lambda state, inputs=[self.app_key, self.app_secret], btn=self.app_info_submit:self.toggle_submit_disabled(inputs, btn))

        # App Authorization
        self.auth_hyperlink = QLabel(f"<a href=\"\">Click here to authorize your app</a>")
        self.auth_hyperlink.setOpenExternalLinks(True)
        self.auth_hyperlink.setContentsMargins(0, 40, 0, 0)
        self.auth_hyperlink.setWordWrap(True)
        layout.addWidget(self.auth_hyperlink)

        self.auth_code_label = QLabel("Auth code")
        self.auth_code_label.setContentsMargins(0, 20, 0, 0)
        layout.addWidget(self.auth_code_label)
        self.auth_code = QLineEdit(self)
        layout.addWidget(self.auth_code)

        self.auth_submit = QPushButton("Authorise")
        self.auth_submit.setDisabled(True)
        self.auth_submit.clicked.connect(self.set_time_zone_visible)
        layout.addWidget(self.auth_submit)

        self.auth_hyperlink.setVisible(False)
        self.auth_code_label.setVisible(False)
        self.auth_code.setVisible(False)
        self.auth_submit.setVisible(False)

        self.auth_code.textChanged.connect(lambda state, inputs=[self.auth_code, parent.dropbox_location.location_line_edit], btn=self.auth_submit : self.toggle_submit_disabled(inputs, btn))
        parent.dropbox_location.location_line_edit.textChanged.connect(lambda state, inputs=[self.auth_code, parent.dropbox_location.location_line_edit], btn=self.auth_submit : self.toggle_submit_disabled(inputs, btn))

        # Time zone
        self.time_zone_label = QLabel("Time zone\nThis will be used to compare sync times.")
        self.time_zone_label.setContentsMargins(0, 40, 0, 0)
        layout.addWidget(self.time_zone_label)

        self.see_time_zones_button = QPushButton("See time zones")
        self.see_time_zones_button.clicked.connect(self.see_time_zones)
        layout.addWidget(self.see_time_zones_button)

        self.time_zone = QLineEdit(self)
        layout.addWidget(self.time_zone)

        self.time_zone_submit = QPushButton("Submit")
        self.time_zone_submit.setDisabled(True)
        self.time_zone_submit.installEventFilter(parent)
        layout.addWidget(self.time_zone_submit)

        self.time_zone_label.setVisible(False)
        self.see_time_zones_button.setVisible(False)
        self.time_zone.setVisible(False)
        self.time_zone_submit.setVisible(False)

        self.time_zone.textChanged.connect(lambda state, tz=self.time_zone, btn=self.time_zone_submit : self.validate_time_zone(tz, btn))

        self.done_label = QLabel("Setup complete")
        self.done_label.setContentsMargins(0, 40, 0, 0)
        layout.addWidget(self.done_label)
        self.done_button = QPushButton("Close")
        self.done_button.installEventFilter(parent)
        layout.addWidget(self.done_button)

        self.done_label.setVisible(False)
        self.done_button.setVisible(False)

    def toggle_submit_disabled(self, inputs: list, btn: QPushButton):
        inputs_all_have_text = True
        for input in inputs:
            input: QLineEdit
            if len(input.text().strip()) == 0:
                inputs_all_have_text = False
                break

        btn.setDisabled(False if inputs_all_have_text else True)


    def set_auth_visible(self):
        auth_link = f"https://www.dropbox.com/oauth2/authorize?client_id={self.app_key.text().strip()}&response_type=code&token_access_type=offline"
        self.auth_hyperlink.setText(f"<a href=\"{auth_link}\">Click here to authorize your app</a>")
        self.auth_hyperlink.setVisible(True)
        self.auth_code_label.setVisible(True)
        self.auth_code.setVisible(True)
        self.auth_submit.setVisible(True)


    def set_time_zone_visible(self):
        self.time_zone_label.setVisible(True)
        self.see_time_zones_button.setVisible(True)
        self.time_zone.setVisible(True)
        self.time_zone_submit.setVisible(True)


    def see_time_zones(self):
        popup = TimeZonesWindow(self)
        popup.exec_()

    def validate_time_zone(self, time_zone: QLineEdit, btn: QPushButton):
        if time_zone.text().strip() in pytz.all_timezones:
            btn.setDisabled(False)
        else:
            btn.setDisabled(True)


    def set_done_visible(self):
        self.done_label.setVisible(True)
        self.done_button.setVisible(True)

    def get_app_info(self) -> tuple[str]:
        return (self.app_key.text().strip(), self.app_secret.text().strip(), self.auth_code.text().strip(), self.time_zone.text().strip())
    

class TimeZonesWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Popup Window")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText('\n'.join(pytz.all_timezones))
        layout.addWidget(self.text_edit)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)