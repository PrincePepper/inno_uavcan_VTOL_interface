import sys

import uavcan
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy, QApplication
from vtol_control_widget import ControlWidget

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


class NodeBlock(QDialog):
    def __init__(self, name: str):
        super().__init__()
        self.label = QLabel(name, self)
        self.fields = [QLabel('Status:', self), QLabel('Data:', self)]
        self.data = [QLabel('0', self), QLabel('0', self)]

    def make_vbox(self, *widgets, stretch_index=None):
        box = QVBoxLayout(self)
        for idx, w in enumerate(widgets):
            box.addWidget(w, 1 if idx == stretch_index else 0)
        box.addStretch(1)
        box.setContentsMargins(0, 0, 0, 0)
        container = QWidget(self)
        container.setLayout(box)
        container.setContentsMargins(0, 0, 0, 0)
        return container

    def make_hbox(self, *widgets, stretch_index=None):
        box = QHBoxLayout(self)
        for idx, w in enumerate(widgets):
            box.addWidget(w, 1 if idx == stretch_index else 0)
        box.addStretch(1)
        box.setContentsMargins(0, 0, 0, 0)
        container = QWidget(self)
        container.setLayout(box)
        container.setContentsMargins(0, 0, 0, 0)
        return container

    def get_widget(self, stretch1, stretch2):
        vlay = QVBoxLayout(self)
        vlay.addStretch(stretch1)
        box = self.make_vbox(self.label,
                             self.make_hbox(self.make_vbox(*self.fields), self.make_vbox(*self.data)))
        box.setStyleSheet("background-color:#ffffff;")
        box.setContentsMargins(5, 5, 5, 5)
        vlay.addWidget(box)
        vlay.addStretch(stretch2)

        container = QWidget(self)
        container.setLayout(vlay)
        container.setContentsMargins(0, 0, 0, 0)
        return container


class VtolWindow(QDialog):
    # def __init__(self, parent, node):
    def __init__(self):
        # super(VtolWindow, self).__init__(parent)
        super(VtolWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle('VTOL Info')

        # self._control_widget = ControlWidget(self, node)
        # self._control_widget = ControlWidget(self, node)
        self._control_widget = ControlWidget(self)

        # self.motor1 = QLabel('Motor1', self)
        # self.motor2 = QLabel('Motor2', self)
        # self.motor3 = QLabel('Motor3', self)
        # self.motor4 = QLabel('Motor4', self)
        # self.engine = QLabel('Engine', self)
        # self.airspeed_sensor = QLabel('Airspeed', self)
        # self.but4 = QPushButton('but4', self)
        # self.but5 = QPushButton('but5', self)
        # self.lbl1 = QLabel()

        # lay1 = QHBoxLayout(self)
        # lay1.addStretch(1)
        # lay1.addWidget(self.but1)
        # lay1.addStretch(5)
        # lay1.addWidget(self.but2)
        # lay1.addStretch(1)
        # lay1.addWidget(self.but3)
        # lay1.addStretch(1)
        # lay1.addWidget(self.lbl1)
        # lay1.addStretch(1)

        # widget1 = QWidget(self)
        # widget1.setLayout(lay1)
        # widget1.setContentsMargins(0, 0, 0, 0)

        # lay2 = QVBoxLayout(self)
        # lay2.addStretch(1)
        # lay2.addWidget(widget1)
        # lay2.addStretch(1)
        # lay2.addWidget(self.but4)
        # lay2.addStretch(4)
        # lay2.addWidget(self.but5)
        # lay2.addStretch(1)

        # widget_output = QWidget(self)
        # widget_output.setLayout(lay2)

        try:
            motor1 = NodeBlock("motor1")
            motor2 = NodeBlock("motor2")
            motor3 = NodeBlock("motor3")
            motor4 = NodeBlock("motor4")

            layout = QHBoxLayout(self)
            layout.addStretch(4)
            layout.addWidget(motor1.get_widget(1, 2))
            layout.addStretch(2)
            layout.addWidget(motor2.get_widget(1, 4))
            layout.addStretch(1)
            layout.addWidget(motor3.get_widget(3, 1))
            layout.addStretch(3)
            layout.addWidget(motor4.get_widget(1, 1))
            layout.addStretch(1)

            self._control_widget.setAlignment(Qt.AlignRight)
            self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

            layout.addWidget(self._control_widget)

            self.setLayout(layout)

            self.show()  # Show the GUI

            # image = QImage('widgets/GUI/res/icons/vtol3.jpg')
            image = QImage('GUI/res/icons/vtol3.jpg')
            h1 = image.width()
            image = image.scaledToHeight(self._control_widget.height())
            h2 = image.width()
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(image))
            self.setPalette(palette)

            margin = layout.getContentsMargins()[0]

            self.resize(int(1280 * h2 / h1) + self._control_widget.width() + margin * 2, image.height())

            self.setFixedWidth(self.width())
            self.setFixedHeight(self.height())

            # self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

            self._status_update_timer = QTimer(self)
            self._status_update_timer.setSingleShot(False)
            self._status_update_timer.timeout.connect(self._nodes_print)
            # self._status_update_timer.start(500)

        except Exception as e:
            print(e)

    def _nodes_print(self):
        nodes = list(self._monitor.find_all(lambda _: True))
        print("Nodes:")
        for e in nodes:
            # self.lbl1.setText(str(e.status.uptime_sec))
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

