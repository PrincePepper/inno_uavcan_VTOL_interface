import logging

import uavcan
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy, QComboBox


from .vtol_control_widget import ControlWidget
from .vtol_subscriber import VtolSubscriber

SCALE = 0.4

logger = logging.getLogger(__name__)

AIRFRAME = {
    'motor1': 50,
    'motor2': 51,
    'motor3': 52,
    'motor4': 53,
    'aileron1': 60,
    'aileron2': 61,
    'pwm': 15
}


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


def make_vbox(*widgets, stretch_index=None, s=1):
    box = QVBoxLayout()
    for idx, w in enumerate(widgets):
        if stretch_index is not None:
            box.addStretch(stretch_index[idx])
        box.addWidget(w)
    box.addStretch(s)
    box.setContentsMargins(0, 0, 0, 0)
    container = QWidget()
    container.setLayout(box)
    container.setContentsMargins(0, 0, 0, 0)
    return container


def make_hbox(*widgets, stretch_index=None, s=1):
    box = QHBoxLayout()
    for idx, w in enumerate(widgets):
        box.addWidget(w, 0 if stretch_index is None else stretch_index[idx])
    box.addStretch(s)
    box.setContentsMargins(0, 0, 0, 0)
    container = QWidget()
    container.setLayout(box)
    container.setContentsMargins(0, 0, 0, 0)
    return container


class NodeBlock(QDialog):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.label = QLabel(name, self)
        self.fields = [QLabel('id:', self), QLabel('Status:', self), QLabel('Data:', self)]
        self.data = [QComboBox(self), QLabel('0', self), QLabel('0', self)]

        if name in AIRFRAME.keys():
            self.data[0].addItem(str(AIRFRAME[name]))
        else:
            self.data[0].addItem("-1")
            print("there is no name in the airframe", name, AIRFRAME.keys())

    def get_widget(self, stretch1=0, stretch2=0):
        vlay = QHBoxLayout(self)
        vlay.addStretch(stretch1)
        box = make_vbox(self.label,
                        make_hbox(make_vbox(*self.fields), make_vbox(*self.data)))
        box.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(box)
        vlay.addStretch(stretch2)

        container = QWidget(self)
        container.setLayout(vlay)
        container.setContentsMargins(0, 0, 0, 0)
        container.setStyleSheet("background-color:#ffffff;")

        return container


class VtolWindow(QDialog):
    def __init__(self, parent, node):
        super(VtolWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle('VTOL Info')

        self.nodes = []

        # motor1 = NodeBlock("motor1")
        motor1 = NodeBlock("pwm")
        motor2 = NodeBlock("motor2")
        motor3 = NodeBlock("motor3")
        motor4 = NodeBlock("motor4")
        aileron1 = NodeBlock("aileron1")
        aileron2 = NodeBlock("aileron2")
        rudder1 = NodeBlock("rudder1")
        rudder2 = NodeBlock("rudder2")
        elevator = NodeBlock("elevator")
        gps = NodeBlock("gps")
        airspeed = NodeBlock("airspeed")
        pressure = NodeBlock("pressure")
        engine = NodeBlock("engine")

        layout = QHBoxLayout(self)

        box1 = make_vbox(rudder1.get_widget(), aileron1.get_widget(), stretch_index=[1, 1], s=3)
        box2 = make_vbox(elevator.get_widget(), motor2.get_widget(), stretch_index=[0, 1], s=6)
        box3 = make_vbox(rudder2.get_widget(), engine.get_widget(), stretch_index=[0, 1], s=10)
        box4 = make_vbox(motor3.get_widget(), gps.get_widget(), motor1.get_widget(), stretch_index=[2, 2, 3], s=6)
        box5 = make_vbox(airspeed.get_widget(), stretch_index=[1], s=1)
        box6 = make_vbox(aileron2.get_widget(), pressure.get_widget(), stretch_index=[1, 2, 1], s=3)
        box7 = make_vbox(motor4.get_widget(), stretch_index=[1], s=2)

        self.blocks = [motor1, motor2, motor3, motor4,
                       aileron1, aileron2, rudder1, rudder2, elevator,
                       gps, airspeed, pressure, engine]

        layout.addStretch(8)
        layout.addWidget(box1)
        layout.addStretch(2)
        layout.addWidget(box2)
        layout.addStretch(2)
        layout.addWidget(box3)
        layout.addStretch(1)
        layout.addWidget(box4)
        layout.addStretch(2)
        layout.addWidget(box5)
        layout.addStretch(0)
        layout.addWidget(box6)
        layout.addStretch(2)
        layout.addWidget(box7)
        layout.addStretch(2)

        self._control_widget = ControlWidget(self, node)
        # self._control_widget = ControlWidget(self)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self._control_widget)

        self.setLayout(layout)

        self.show()
        margin = layout.getContentsMargins()[0]

        image = QImage('widgets/GUI/res/icons/vtol3.jpg')
        # image = QImage('GUI/res/icons/vtol3.jpg')
        h1 = image.width()
        image = image.scaledToHeight(self._control_widget.height())
        h2 = image.width()
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(image))
        self.setPalette(palette)



        self.resize(int(1280 * h2 / h1) + self._control_widget.width() + margin * 2, image.height())

        self.setFixedWidth(self.width())
        self.setFixedHeight(self.height())

        self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._nodes_print)
        # self._status_update_timer.start(200)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._update_combo_boxes)
        self._status_update_timer.start(500)

        self.sub = VtolSubscriber(node)

    def _update_combo_boxes(self):
        nodes = list(e.node_id for e in self._monitor.find_all(lambda _: True))
        if nodes != self.nodes:
            self.nodes = nodes
            for block in self.blocks:
                if block.name not in AIRFRAME.keys():
                    first = -1
                else:
                    first = AIRFRAME[block.name]
                n = [*nodes]
                if first in n:
                    n.remove(first)
                block.data[0].clear()
                block.data[0].addItem(str(first))
                block.data[0].addItems(str(i) for i in n)

    def _nodes_print(self):
        if self.sub.has_next():
            text = self.sub.next()
            print(text[0].source_node_id)
            print(text[0].payload.voltage)
            print(text[1])
        # nodes = list(self._monitor.find_all(lambda _: True))
        # print("Nodes:")
        # for e in nodes:
        #     # self.lbl1.setText(str(e.status.uptime_sec))
        #     print("NID:", e.node_id)
        #     print("Name", e.info.name if e.info else '?')
        #     print("Mode", e.status.mode)
        #     print("Health", e.status.health)
        #     print("Uptime", e.status.uptime_sec)
        #     print("VSSC", render_vendor_specific_status_code(e.status.vendor_specific_status_code))
        # print()

# app = QApplication(sys.argv)
# window = VtolWindow()
# app.exec_()