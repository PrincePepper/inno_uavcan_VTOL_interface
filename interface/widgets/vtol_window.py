# from PyQt5 import uic
import copy
import sys

import uavcan
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget, QApplication, QSizePolicy, \
    QMainWindow
from vtol_control_widget import ControlWidget
from win32api import GetSystemMetrics

SCALE = 0.4


def render_vendor_specific_status_code(s):
    out = '%-5d     0x%04x\n' % (s, s)
    binary = bin(s)[2:].rjust(16, '0')

    def high_nibble(s):
        return s.replace('0', '\u2070').replace('1', '\u00B9')  # Unicode 0/1 superscript

    def low_nibble(s):
        return s.replace('0', '\u2080').replace('1', '\u2081')  # Unicode 0/1 subscript

    nibbles = [
        high_nibble(binary[:4]),
        low_nibble(binary[4:8]),
        high_nibble(binary[8:12]),
        low_nibble(binary[12:]),
    ]

    out += ''.join(nibbles)
    return out


class VtolWindow(QMainWindow):
    # def __init__(self, parent, node):
    def __init__(self):
        # super(VtolWindow, self).__init__(parent)
        super(VtolWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle('VTOL Info')

        # self._control_widget = ControlWidget(self, node)
        self._control_widget = ControlWidget(self)

        self._old_height = 0
        self._old_width = 0

        self.but1 = QPushButton('but1', self)
        self.but2 = QPushButton('but2', self)
        self.but3 = QPushButton('but3', self)
        self.but4 = QPushButton('but4', self)
        self.but5 = QPushButton('but5', self)
        self.lbl1 = QLabel()

        lay1 = QHBoxLayout(self)
        lay1.addStretch(1)
        lay1.addWidget(self.but1)
        lay1.addStretch(5)
        lay1.addWidget(self.but2)
        lay1.addStretch(1)
        lay1.addWidget(self.but3)
        lay1.addStretch(1)
        lay1.addWidget(self.lbl1)
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

        widget_output = QWidget(self)
        # widget_output.setStyleSheet("background-image: url(GUI/res/icons/vtol2.jpg); background-repeat: no-repeat;")
        # widget_output.setAutoFillBackground(False)
        widget_output.setLayout(lay2)

        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)
        self.setStyleSheet("VtolWindow {background-image: url(GUI/res/icons/vtol2.jpg); background-repeat: no-repeat;}")

        layout = QHBoxLayout(self.centralwidget)
        layout.addWidget(widget_output)
        # layout.addStretch(1)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self._control_widget)

        self.setLayout(layout)

        self.show()  # Show the GUI

        # Setting up background image
        # image = QImage('widgets/GUI/res/icons/vtol3.jpg').scaledToWidth(int(GetSystemMetrics(0) * SCALE))
        # image = QImage('GUI/res/icons/vtol3.jpg').scaledToHeight(int(GetSystemMetrics(1) * SCALE))
        margin = layout.getContentsMargins()[0]

        # image = QImage('GUI/res/icons/vtol3.jpg')
        # h1 = image.height()
        # image = image.scaledToHeight(self._control_widget.height() + margin * 2)
        # h2 = image.height()

        # palette = QPalette()
        # palette.setBrush(QPalette.Window, QBrush(image))

        # self.setPalette(palette)
        # self.resize(int(1280 * h2 / h1) + self._control_widget.width() + margin * 2, image.height())

        # self.setFixedWidth(self.width())
        # self.setFixedHeight(self.height())

        # self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._nodes_print)
        # self._status_update_timer.start(500)

    def _nodes_print(self):
        nodes = list(self._monitor.find_all(lambda _: True))
        print("Nodes:")
        for e in nodes:
            self.lbl1.setText(str(e.status.uptime_sec))
            print("NID:", e.node_id)
            print("Name", e.info.name if e.info else '?')
            print("Mode", e.status.mode)
            print("Health", e.status.health)
            print("Uptime", e.status.uptime_sec)
            print("VSSC", render_vendor_specific_status_code(e.status.vendor_specific_status_code))
        print()


app = QApplication(sys.argv)
window = VtolWindow()
app.exec_()

