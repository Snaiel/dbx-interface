from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QScrollArea, QFrame
from PyQt5.QtCore import pyqtSignal, QObject, QEvent, Qt, QPoint
from PyQt5.QtGui import QColor, QPainter, QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from pathlib import Path
from package.ui.widgets.explorers.explorer import Explorer
from enum import Enum

class ActionItemStatus(Enum):
    QUEUED = 1
    RUNNING = 2
    DONE = 3

class ActionStatusPopup(QWidget):

    close_signal = pyqtSignal()

    def __init__(self, parent, explorer: Explorer):
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

        self.close_btn = QSvgWidget(str(Path(Path(__file__).parents[1], 'icons', "x.svg")), self.central_widget)
        self.close_btn.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.close_btn.setFixedWidth(20)
        self.close_btn.installEventFilter(self)
        self.close_btn.setStyleSheet(
            "QWidget::hover {"
            "background-color: #D2D2D2;"
            "border-radius: 2px;"
            "}"
        )

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
            self.list_layout.addWidget(ActionStatusPopup.ActionItem(self, f"Action {i}"))

        self.actions_list.setWidget(self.list_widget)

        self.central_widget.move(self.rect().center() - QPoint(int(self.central_widget.width() / 2), int(self.central_widget.height() / 2)))

        explorer.installEventFilter(self)

        self.hide()

    def paintEvent(self, event):
        # dim the background
        s = self.explorer.size()
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(self.fillColor)
        qp.setPen(QColor(0, 0, 0, 0))
        qp.drawRect(0, 0, s.width(), s.height())

        return super().paintEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        central_rect = self.central_widget.rect()
        central_rect.translate(self.central_widget.pos())
        if not central_rect.contains(event.pos()):
            # self.close_signal.emit()
            self.hide()

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if object == self.close_btn and event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                # self.close_signal.emit()
                self.hide()
        elif object == self.explorer and event.type() == QEvent.Type.Resize:
            self.resize(self.explorer.size())
            self.central_widget.move(self.rect().center() - QPoint(int(self.central_widget.width() / 2), int(self.central_widget.height() / 2)))
        return False

    def toggle(self):
        if self.pos() != self.explorer.pos():
            self.move(self.explorer.pos())
            
        if self.isHidden():
            self.show()
        else:
            self.hide()

    class ActionItem(QWidget):
        def __init__(self, parent, action_label):
            super().__init__(parent)

            self.setStyleSheet("QWidget::hover"
                            "{"
                            "background-color: #D2D2D2;"
                            "}")

            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

            self.item_layout = QHBoxLayout(self)
            self.item_layout.setContentsMargins(8, 4, 8, 4)
            
            self.icon = QSvgWidget(str(Path(Path(__file__).parents[1], 'icons', "clock.svg")))
            self.icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            self.icon.setMinimumWidth(12)

            self.label = QLabel(action_label)

            self.item_layout.addWidget(self.label)
            self.item_layout.addSpacing(140)
            self.item_layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignRight)