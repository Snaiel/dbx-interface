from PyQt5.QtWidgets import QDialog, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout
from collections.abc import Iterable
from dropbox import Dropbox
from dropbox.files import DeleteArg, DeleteBatchLaunch

class DeleteNonExistent(QDialog):
    def __init__(self, dbx: Dropbox, paths_to_delete: Iterable):
        super().__init__()
        
        self.dbx = dbx
        self.paths_to_delete = paths_to_delete

        self.setWindowTitle("Delete Non-Existent Paths")

        label1 = QLabel('Local paths assumed to be deleted:')

        # Create a multi-line text area
        multiline_text = QTextEdit()
        multiline_text.setReadOnly(True)
        multiline_text.setText("\n".join(paths_to_delete))

        label2 = QLabel('Delete the corresponding paths in the cloud?')

        # Create two buttons
        close_button = QPushButton('No')
        delete_button = QPushButton('Delete')

        button_layout = QHBoxLayout()
        button_layout.addWidget(close_button)
        button_layout.addWidget(delete_button)

        # Create a layout to arrange the widgets
        layout = QVBoxLayout()
        layout.addWidget(label1)
        layout.addWidget(multiline_text)
        layout.addWidget(label2)
        layout.addLayout(button_layout)

        # Set the layout for the dialog
        self.setLayout(layout)

        # Set up event handlers for the buttons
        close_button.clicked.connect(self.close)
        delete_button.clicked.connect(self.delete_paths)

        self.setMinimumWidth(1000)

    def delete_paths(self):
        entries = []
        for path in self.paths_to_delete:
            entries.append(DeleteArg(path))
        id: DeleteBatchLaunch = self.dbx.files_delete_batch(entries)
        print(f"Deleting paths... Job ID: {id.get_async_job_id()}")
        self.close()