from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QPixmap, QPainter, QBrush, QColor

class RectangleSelectionBackground(QWidget):

    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal(QMouseEvent)
    rectangle_select = pyqtSignal(QRect, bool)

    def __init__(self, parent):
        super().__init__(parent)

        self.pix = QPixmap(self.rect().size())
        self.pix.fill(Qt.GlobalColor.transparent)

        self.begin, self.destination = QPoint(), QPoint()
        self.selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.pix)
        if not self.begin.isNull() and not self.destination.isNull() and self.selecting:
            rect = QRect(self.begin, self.destination)
            painter.fillRect(rect.normalized(), QBrush(QColor(210, 210, 210)))

    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.begin = event.pos()
            self.destination = self.begin
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.destination = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.selecting = False
        if event.button() == Qt.MouseButton.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            deselect = False
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                deselect = True
            rect = QRect(self.begin, self.destination)
            self.rectangle_select.emit(rect, deselect)
            self.left_clicked.emit()
            painter = QPainter(self.pix)
            painter.fillRect(rect.normalized(), QBrush(Qt.GlobalColor.transparent))
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(event)
        self.update()