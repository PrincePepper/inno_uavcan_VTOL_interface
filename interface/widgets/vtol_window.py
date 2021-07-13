# from PyQt5 import uic
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QPushButton, QHBoxLayout, QWidget
from win32api import GetSystemMetrics

SCALE = 0.5

class VtolWindow(QDialog):
    # def __init__(self, parent, node):

    resized = QtCore.pyqtSignal()

    def __init__(self):
        # super(VtolWindow, self).__init__(parent)
        super(VtolWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle('VTOL Info')

        self._old_height = 0
        self._old_width = 0

        self.but1 = QPushButton('but1', self)
        self.but2 = QPushButton('but2', self)
        self.but3 = QPushButton('but3', self)
        self.but4 = QPushButton('but4', self)
        self.but5 = QPushButton('but5', self)

        # Setting up background image
        image = QImage('GUI/res/icons/vtol2.jpg').scaledToWidth(int(GetSystemMetrics(0) * SCALE))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(image))
        self.setPalette(palette)
        self.resize(image.width(), image.height())

        lay1 = QHBoxLayout(self)
        lay1.addStretch(1)
        lay1.addWidget(self.but1)
        lay1.addStretch(1)
        lay1.addWidget(self.but2)
        lay1.addStretch(1)
        lay1.addWidget(self.but3)
        lay1.addStretch(1)

        widget1 = QWidget(self)
        widget1.setLayout(lay1)
        widget1.setContentsMargins(0, 0, 0, 0)

        lay2 = QVBoxLayout(self)
        lay2.addStretch(1)
        lay2.addWidget(widget1)
        lay2.addStretch(1)
        lay2.addWidget(self.but4)
        lay2.addStretch(4)
        lay2.addWidget(self.but5)
        lay2.addStretch(1)

        # left, top, right, bottom = lay2.getContentsMargins()
        # lay2.setContentsMargins(left, top, right, bottom)

        self.setLayout(lay2)

        self.show()  # Show the GUI

        self.setFixedWidth(self.width())
        self.setFixedHeight(self.height())


app = QApplication(sys.argv)
window = VtolWindow()
app.exec_()

