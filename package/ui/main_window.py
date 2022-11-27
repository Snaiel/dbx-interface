from package.ui.widgets.dbx_explorer import DropboxExplorer
from package.ui.widgets.local_explorer import LocalExplorer
from package.model.dbx_model import DropboxModel
from package.model.local_model import LocalModel
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QShortcut, QStatusBar, QHBoxLayout, QVBoxLayout, QSizePolicy, QScrollArea, QFrame
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QEvent, Qt, QRect, QPoint
from PyQt5.QtGui import QKeySequence, QColor, QPainter, QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self, dbx, local_root):
        super().__init__()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        # Status Bar
        self.status_bar = MainWindow.StatusBar()
        self.status_bar.cloud.action_label_clicked.connect(self._onpopup)
        self.setStatusBar(self.status_bar)

        # Dropbox Interface
        self.dbx_model = DropboxModel(dbx)
        self.dbx_model.action_update.connect(self.status_bar.update_action_status)

        self.dbx_explorer = DropboxExplorer(central_widget, self.dbx_model)
        self.dbx_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        central_layout.addWidget(self.dbx_explorer, 0, 0)
        self.dbx_explorer.left_clicked.connect(self.explorer_focus)

        # Local Interface
        self.local_model = LocalModel()
        self.local_model.action_update.connect(self.status_bar.update_action_status)

        self.local_explorer = LocalExplorer(central_widget, self.local_model, local_root)
        self.local_explorer.selection_num_changed.connect(self.status_bar.update_num_selected)
        central_layout.addWidget(self.local_explorer, 0, 1)
        central_layout.setSpacing(0)
        self.local_explorer.left_clicked.connect(self.explorer_focus)

        self.focused_explorer = self.dbx_explorer

        central_layout.setColumnStretch(0, 1)
        central_layout.setColumnStretch(1, 1)

        self._create_shortcuts()

    def _create_shortcuts(self):
        select_all = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        select_all.activated.connect(lambda: self.focused_explorer.item_list.select_all())

        deselect_all = QShortcut(QKeySequence("Ctrl+D"), self)
        deselect_all.activated.connect(lambda: self.focused_explorer.item_list.deselect_all())

    @pyqtSlot(QWidget)
    def explorer_focus(self, widget: QWidget):
        self.focused_explorer = widget

    @pyqtSlot()
    def _onpopup(self):
        self._popframe = MainWindow.ActionStatusPopup(self, self.dbx_explorer)
        self._popframe.move(0, 0)
        # self._popframe.resize(self.width(), self.height())
        # self._popframe.SIGNALS.CLOSE.connect(self._closepopup)
        self._popflag = True
        self._popframe.show()

    class ActionStatusPopup(QWidget):

        close_signal = pyqtSignal()

        def __init__(self, parent, explorer):
            super().__init__(parent)

            self.explorer = explorer

            self.resize(explorer.size())

            # make the window frameless
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

            self.fillColor = QColor(30, 30, 30, 100)

            self.central_widget = QWidget(self)
            self.central_widget.setObjectName("central_widget")
            self.central_widget.setFixedSize(300, 300)
            self.central_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.central_widget.setStyleSheet(
                'QWidget#central_widget {'
                'background: palette(window);'
                'border-radius: 4px'
                '}'
            )

            self.central_layout = QGridLayout(self.central_widget)

            self.header = QLabel(self.central_widget, text="Actions")
            self.header.setFixedWidth(100)
            self.header.setStyleSheet(
                "padding: 2px 2px;"
                "font-weight: 500;"
            )

            self.close_btn = QSvgWidget(str(Path(Path(__file__).parent, 'widgets', 'icons', "x.svg")), self.central_widget)
            self.close_btn.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            self.close_btn.setFixedWidth(20)

            self.central_layout.addWidget(self.header, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
            self.central_layout.addWidget(self.close_btn, 0, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

            self.actions_list = QScrollArea()
            self.actions_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.actions_list.setFrameShape(QFrame.Shape.Box)
            self.central_layout.addWidget(self.actions_list, 1, 0, 1, 2)

            self.list_widget = QWidget(self.actions_list)
            self.list_layout = QVBoxLayout(self.list_widget)
            self.list_widget.setLayout(self.list_layout)

            for i in range(15):
                self.list_layout.addWidget(QLabel(f"bruh {i}"))

            self.actions_list.setWidget(self.list_widget)

            self.central_widget.move(self.rect().center() - QPoint(int(self.central_widget.width() / 2), int(self.central_widget.height() / 2)))

        def paintEvent(self, event):
            # dim the background
            s = self.explorer.size()
            qp = QPainter()
            qp.begin(self)
            # qp.setRenderHint(QPainter.Antialiasing, True)
            qp.setBrush(self.fillColor)
            qp.setPen(QColor(0, 0, 0, 0))
            qp.drawRect(0, 0, s.width(), s.height())

            return super().paintEvent(event)

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            print(self.central_widget.rect().contains(event.pos()))

        def _onclose(self):
            print("Close")
            self.close_signal.emit()

    class StatusBar(QStatusBar):
        def __init__(self):
            super().__init__()

            self.showMessage("")

            self.cloud = MainWindow.StatusBar.StatusBarSection()
            self.local = MainWindow.StatusBar.StatusBarSection()

            self.addWidget(self.cloud, 21)
            self.addWidget(self.local, 20)

        @pyqtSlot(QObject, int)
        def update_num_selected(self, explorer: QObject, num: int):
            statusbar_section = self._get_statusbar_section(explorer) # type: MainWindow.StatusBar.StatusBarSection
            statusbar_section.set_num_selected(num)

        @pyqtSlot(QObject, str)
        def update_action_status(self, model: QObject, message: str):
            statusbar_section = self._get_statusbar_section(model) # type: MainWindow.StatusBar.StatusBarSection
            statusbar_section.set_action_status(message)

        def _get_statusbar_section(self, origin: QObject):
            statusbar_section = None
            if isinstance(origin, DropboxExplorer) or isinstance(origin, DropboxModel):
                statusbar_section = self.cloud
            elif isinstance(origin, LocalExplorer) or isinstance(origin, LocalModel):
                statusbar_section = self.local
            return statusbar_section

        class StatusBarSection(QWidget):
            action_label_clicked = pyqtSignal()
            def __init__(self):
                super().__init__()

                self.section_layout = QHBoxLayout()
                self.section_layout.setContentsMargins(0, 0, 0, 0)
                self.setLayout(self.section_layout)
                
                self.num_selected = QLabel("0 items selected")
                self.action_status = QLabel("no actions performed")
                self.action_status.setStyleSheet("QWidget::hover"
                            "{"
                            "background-color: #D2D2D2;"
                            "}")

                self.action_status.installEventFilter(self)

                self.section_layout.addWidget(self.num_selected)
                self.section_layout.addWidget(self.action_status)

            def set_num_selected(self, num: int):
                self.num_selected.setText(f"{num} items selected")

            def set_action_status(self, message: str):
                self.action_status.setText(message)

            def eventFilter(self, object: QObject, event: QEvent) -> bool:
                if object == self.action_status and event.type() == QEvent.Type.MouseButtonRelease:
                    self.action_label_clicked.emit()
                return False    