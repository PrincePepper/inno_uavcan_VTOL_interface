import json
import logging

import numpy
import uavcan
from PIL import Image, ImageQt
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy, QComboBox, QFileDialog

from .vtol_control_widget import ControlWidget
from .vtol_subscriber import VtolSubscriber

SCALE = 0.4

logger = logging.getLogger(__name__)

update = False

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


def make_vbox(*widgets, stretch_index=None, s=1, margin=False):
    box = QVBoxLayout()
    for idx, w in enumerate(widgets):
        if stretch_index is not None:
            box.addStretch(stretch_index[idx])
        box.addWidget(w)
    box.addStretch(s)
    container = QWidget()
    container.setLayout(box)
    if margin:
        m = int(box.getContentsMargins()[0] / 2)
        container.setContentsMargins(m, m, m, m)
    else:
        container.setContentsMargins(0, 0, 0, 0)
    box.setContentsMargins(0, 0, 0, 0)
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


def node_health_to_str_color(health):
    return {
        0: ("OK", "color: green"),
        1: ("WARNING", "color: orange"),
        2: ("ERROR", "color: magenta"),
        3: ("CRITICAL", "color: red"),
    }.get(health)


class NodeBlock(QDialog):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.label = QLabel(name, self)
        self.status = QLabel("", self)
        self.fields = [QLabel('id:', self), QLabel('Health:', self), QLabel('Data:', self)]

        self.combo_box = QComboBox(self)
        self.combo_box.activated[str].connect(self.on_changed)
        self.data = [self.combo_box, QLabel('0', self), QLabel('0', self)]
        self.voltage_lbl = QLabel('-', self)
        self.current_lbl = QLabel('-', self)
        self.widget = None

        self.id = -1
        if name in AIRFRAME.keys():
            self.id = AIRFRAME[name]

        self.combo_box.addItem(str(self.id))

        self.make_widget()

    def set_voltage(self, v):
        if type(v) == str:
            self.voltage_lbl.setText(v)
        else:
            self.voltage_lbl.setText(str("{:1.2f}".format(v)) + 'V')

    def set_current(self, i):
        if type(i) == str:
            self.current_lbl.setText(i)
        else:
            self.current_lbl.setText(str("{:1.2f}".format(i)) + 'A')

    def set_health(self, h):
        text, style = node_health_to_str_color(h)
        self.data[1].setText(text)
        self.data[1].setStyleSheet(style)

    def on_changed(self, text):
        global update  # , AIRFRAME
        # AIRFRAME[self.name] = int(text)
        self.id = int(text)
        update = True

    def make_widget(self):
        box = make_vbox(make_hbox(self.label, self.status),
                        make_hbox(make_vbox(*self.fields), make_vbox(*self.data)),
                        make_hbox(self.voltage_lbl, self.current_lbl, stretch_index=[1, 0], s=0), margin=True)
        box.setStyleSheet("background-color: white;")
        self.widget = box


class VtolWindow(QDialog):
    def __init__(self, parent, node):
        super(VtolWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        try:
            with open('airframe.json', 'r') as f:
                global AIRFRAME
                AIRFRAME = json.load(f)
        except FileNotFoundError:
            pass

        self.setWindowTitle('VTOL Info')

        self.nodes_id = []

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

        box1 = make_vbox(rudder1.widget, aileron1.widget, stretch_index=[1, 1], s=3)
        box2 = make_vbox(elevator.widget, motor2.widget, stretch_index=[0, 1], s=6)
        box3 = make_vbox(rudder2.widget, engine.widget, stretch_index=[0, 1], s=10)
        box4 = make_vbox(motor3.widget, gps.widget, motor1.widget, stretch_index=[2, 2, 3], s=6)
        box5 = make_vbox(airspeed.widget, stretch_index=[1], s=1)
        box6 = make_vbox(aileron2.widget, pressure.widget, stretch_index=[1, 2, 1], s=3)
        box7 = make_vbox(motor4.widget, stretch_index=[1], s=2)

        self.blocks = [motor1, motor2, motor3, motor4,
                       aileron1, aileron2, rudder1, rudder2, elevator,
                       gps, airspeed, pressure, engine]

        layout = QHBoxLayout(self)
        layout.addStretch(18)
        layout.addWidget(box1)
        layout.addStretch(6)
        layout.addWidget(box2)
        layout.addStretch(4)
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

        self._control_widget = ControlWidget(self, node, self.save_file)
        # self._control_widget = ControlWidget(self)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # self._save_button = QPushButton('Save airframe', self)
        # self._save_button.setFocusPolicy(Qt.NoFocus)
        # self._save_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # self._save_button.clicked.connect(self.save_file)

        # right_vbox = make_vbox(self._save_button, self._control_widget)

        layout.addWidget(self._control_widget)

        self.setLayout(layout)

        self.show()
        margin = layout.getContentsMargins()[0]

        jpeg = numpy.asarray(Image.open('widgets/GUI/res/icons/vtol.jpg'))
        x = jpeg.shape[1]
        y = jpeg.shape[0]
        new = numpy.zeros((y, x + 4000, 3))
        new[:y, :x, :3] = jpeg
        new[:y, x:, :3] = float(255)
        image = Image.fromarray(numpy.uint8(new))
        # Image turn to QImage
        image = ImageQt.ImageQt(image)
        h1 = image.height()
        image = image.scaledToHeight(self._control_widget.height() + margin * 2)
        h2 = image.height()
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(image))
        self.setPalette(palette)

        self.resize(int(x * h2 / h1) + self._control_widget.width() + margin * 2, image.height())

        self.setFixedWidth(self.width())
        self.setFixedHeight(self.height())

        self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._nodes_update)
        self._status_update_timer.start(100)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._update_combo_boxes)
        self._status_update_timer.start(500)

        self.subscriber = VtolSubscriber(node)

    def save_file(self):
        global AIRFRAME
        name = QFileDialog.getSaveFileName(self, 'Save File', "airframe.json")
        AIRFRAME = {}
        for block in self.blocks:
            AIRFRAME[block.name] = block.id
        with open(name[0], 'w') as f:
            json.dump(AIRFRAME, f)

    def _update_combo_boxes(self):
        global update
        nodes = self._monitor.find_all(lambda _: True)
        nodes_id = list(e.node_id for e in nodes)
        if nodes_id != self.nodes_id or update:
            update = False
            self.nodes_id = nodes_id
            for block in self.blocks:
                first = block.id
                n = [*nodes_id]
                if first in n:
                    n.remove(first)
                    block.status.setText("connect")
                    block.status.setStyleSheet("color:green;")
                else:
                    block.status.setText("nc")
                    block.status.setStyleSheet("color:red;")
                    block.set_voltage('-')
                    block.set_current('-')
                block.combo_box.clear()
                block.combo_box.addItem(str(first))
                block.combo_box.addItems(str(i) for i in n)

    def _nodes_update(self):
        if self.subscriber.has_next():
            nodes = self._monitor.find_all(lambda _: True)
            nodes_health = {k.node_id: k.status.health for k in nodes}

            data = self.subscriber.next()
            node_id = data[0].source_node_id
            for block in filter(lambda a: a.id == node_id, self.blocks):
                block.set_voltage(data[0].payload.voltage)
                block.set_current(data[0].payload.current)
                block.set_health(nodes_health[block.id])
            # print(data[0].source_node_id)
            # print(data[0].payload.voltage)
            print(data[0])
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
# window = VtolWindow(1)
# app.exec_()
