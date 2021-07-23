import json
import logging

import numpy
import uavcan
from PIL import Image, ImageQt
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy, \
    QComboBox, QFileDialog, QMessageBox, QPushButton

from . import request_confirmation, show_error
from .dynamic_node_id_allocator import DynamicNodeIDAllocatorWidget
from .file_server import FileServerWidget
from .node_monitor import NodeMonitorWidget
from .node_properties import NodePropertiesWindow
from .vtol_control_widget import ControlWidget
from .vtol_subscriber import VtolSubscriber

REQUEST_PRIORITY = 30
global node_block_properties
global AIRFRAME
global circuit_subscriber  # not all devices transmit current and voltage
global main_node  # provides access to nodes throughout the file

check_status_update = False

logger = logging.getLogger(__name__)


# method that allows you to more quickly draw elements vertically
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


# method that allows you to more quickly draw elements horizontally
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


# node life signatures
def node_health_to_str_color(health):
    return {
        -1: ("-", "color: black"),
        0: ("OK", "color: green"),
        1: ("WARNING", "color: orange"),
        2: ("ERROR", "color: magenta"),
        3: ("CRITICAL", "color: red"),
    }.get(health)


class NodeBlockProperties:
    def __init__(self, node, widget, file_server_widget, node_monitor_widget,
                 dynamic_node_id_allocation_widget):
        self._node_windows = {}
        self._node = node
        self.widget = widget
        self._file_server_widget = file_server_widget
        self._node_monitor_widget = node_monitor_widget
        self._dynamic_node_id_allocation_widget = dynamic_node_id_allocation_widget

    def on_properties_clicked(self, node_id):
        if node_id in self._node_windows:
            # noinspection PyBroadException
            try:
                self._node_windows[node_id].close()
                self._node_windows[node_id].setParent(None)
                self._node_windows[node_id].deleteLater()
            except Exception:
                # TODO: Sometimes fails with
                #  "wrapped C/C++ object of type NodePropertiesWindow has been deleted"
                #  This needs to be fixed somehow, and why the error pops out ¯\_(ツ)_/¯
                pass
            del self._node_windows[node_id]

        w = NodePropertiesWindow(self.widget, self._node, node_id, self._file_server_widget,
                                 self._node_monitor_widget.monitor,
                                 self._dynamic_node_id_allocation_widget)
        w.show()
        self._node_windows[node_id] = w


class NodeBlock(QDialog):
    def __init__(self, name: str):
        super().__init__()

        self.name = name
        self.temp_data_fields = None

        global main_node
        self._node = main_node

        global AIRFRAME

        # lists for our output
        self.subscriptions = []
        self.to_subscribe = []
        self.to_subscribe_parametr = []

        self.label = QLabel(name, self)
        self.status = QLabel("", self)
        self.combo_box = QComboBox(self)
        self.combo_box.activated[str].connect(self._on_changed)
        # get the name of the fields and what it stores
        self.fields, self.data = self.parse_fields(AIRFRAME)

        self.set_subscribe()

        self.voltage_lbl = QLabel('-', self)
        self.current_lbl = QLabel('-', self)

        self.properties_button = QPushButton('Properties', self)
        self.properties_button.setFocusPolicy(Qt.NoFocus)
        self.properties_button.clicked.connect(self.on_clicked)
        self.properties_button.setEnabled(False)

        self.widget = None

        self.id = -1
        if name in AIRFRAME.keys():
            self.id = int(AIRFRAME[name]["id"])
        self.combo_box.addItem(str(self.id))

        self.voltage_and_current_box = make_hbox(self.voltage_lbl,
                                                 self.current_lbl,
                                                 stretch_index=[1, 0],
                                                 s=0)
        self.voltage_and_current_box.hide()
        self.make_widget()

    def parse_fields(self, fields):
        list_fields = []
        list_data = []

        # all nodes have status bar and id
        list_fields.append(QLabel('id:', self))
        list_data.append(self.combo_box)
        list_fields.append(QLabel('Health:', self))
        list_data.append(QLabel('0', self))

        if self.name in AIRFRAME.keys():
            self.temp_data_fields = AIRFRAME[self.name]
            for i in self.temp_data_fields:
                if i != "id":
                    list_fields.append(QLabel(str(i), self))
                    list_data.append(QLabel("0", self))
                    split_temp_data_fields = self.temp_data_fields[i].split()
                    self.to_subscribe.append(split_temp_data_fields[0])
                    self.to_subscribe_parametr.append(split_temp_data_fields[1])

        return list_fields, list_data

    def update_data(self, nodes, nodes_health):
        for i, sub in enumerate(self.subscriptions):
            if sub.has_next():
                data = sub.next()
                node_id = data[0].source_node_id
                if self.id == node_id:
                    self.set_health(nodes_health[node_id])
                    global circuit_subscriber
                    if circuit_subscriber.has_next():
                        data_circuit = circuit_subscriber.next()
                        self.set_voltage(data_circuit[0].payload.voltage)
                        self.set_current(data_circuit[0].payload.current)

                    self.data[i + 2].setText(
                        str("{:1.2f}".format(
                            eval(f"data[0].payload.{self.to_subscribe_parametr[i]}"))))

            else:
                # if the data type does not match the given id, then it will report it
                global check_status_update
                if check_status_update:
                    self.data[i + 2].setText('error')

    def set_subscribe(self):
        for i in self.to_subscribe:
            self.subscriptions.append(VtolSubscriber(self._node, i))

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

    def on_clicked(self):
        global node_block_properties
        node_block_properties.on_properties_clicked(self.id)

    def _on_changed(self, text):
        global check_status_update
        self.id = int(text)
        check_status_update = True
        global circuit_subscriber
        if circuit_subscriber.has_next():
            data = circuit_subscriber.next()
            node_id = data[0].source_node_id
            if self.id == node_id:
                self.voltage_and_current_box.show()
        else:
            self.voltage_and_current_box.hide()

    def make_widget(self):
        box = make_vbox(make_hbox(self.label, self.status),
                        make_hbox(make_vbox(*self.fields), make_vbox(*self.data)),
                        self.properties_button,
                        self.voltage_and_current_box, margin=True)
        #
        # TODO: make a normal node styling
        #
        box.setStyleSheet("background-color: white;")
        self.widget = box


class VtolWindow(QDialog):
    def __init__(self, parent, node):
        super(VtolWindow, self).__init__(parent)
        self.setWindowTitle('VTOL Info')

        self._file_server_widget = FileServerWidget(self, node)
        global main_node
        main_node = node
        self._node = node
        self.nodes_id = []

        self._node_monitor_widget = NodeMonitorWidget(self, node)
        # self._node_monitor_widget.on_info_window_requested = self._show_node_window

        self._dynamic_node_id_allocation_widget = DynamicNodeIDAllocatorWidget(self, node,
                                                                               self._node_monitor_widget.monitor)

        global node_block_properties
        node_block_properties = NodeBlockProperties(node, self, self._file_server_widget,
                                                    self._node_monitor_widget,
                                                    self._dynamic_node_id_allocation_widget)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # check for the existence of the configuration file otherwise use the default settings
        try:
            with open('airframe.json', 'r') as f:
                global AIRFRAME
                AIRFRAME = json.load(f)
        except FileNotFoundError:
            dic = {"motor_1": {"id": -1}, "motor_2": {"id": -1}, "motor_3": {"id": -1},
                   "motor_4": {"id": -1},
                   "aileron_1": {"id": -1}, "aileron_2": {"id": -1}, "rudder_1": {"id": -1},
                   "rudder_2": {"id": -1},
                   "elevator": {"id": -1}, "gps": {"id": -1}, "airspeed": {"id": -1},
                   "pressure": {"id": -1},
                   "engine": {"id": -1}, "_control_widjet": {"eleron": -1}}
            AIRFRAME = dic
            with open('airframe.json', 'w') as outfile:
                json.dump(dic, outfile)

        motor1 = NodeBlock("motor_1")
        motor2 = NodeBlock("motor_2")
        motor3 = NodeBlock("motor_3")
        motor4 = NodeBlock("motor_4")
        aileron1 = NodeBlock("aileron_1")
        aileron2 = NodeBlock("aileron_2")
        rudder1 = NodeBlock("rudder_1")
        rudder2 = NodeBlock("rudder_2")
        elevator = NodeBlock("elevator")
        gps = NodeBlock("gps")
        airspeed = NodeBlock("airspeed")
        pressure = NodeBlock("pressure")
        engine = NodeBlock("engine")

        self.box_1 = make_vbox(rudder1.widget, aileron1.widget, stretch_index=[1, 1], s=3)
        self.box_2 = make_vbox(elevator.widget, motor2.widget, stretch_index=[0, 1], s=6)
        self.box_3 = make_vbox(rudder2.widget, engine.widget, stretch_index=[0, 1], s=10)
        self.box_4 = make_vbox(motor3.widget, gps.widget, motor1.widget, stretch_index=[2, 2, 3],
                               s=6)
        self.box_5 = make_vbox(airspeed.widget, stretch_index=[1], s=1)
        self.box_6 = make_vbox(aileron2.widget, pressure.widget, stretch_index=[1, 2, 1], s=3)
        self.box_7 = make_vbox(motor4.widget, stretch_index=[1], s=2)

        self.blocks = [motor1, motor2, motor3, motor4,
                       aileron1, aileron2, rudder1, rudder2, elevator,
                       gps, airspeed, pressure, engine]

        layout = QHBoxLayout(self)
        listStretch = [18, 6, 4, 1, 2, 0, 2]
        listWidget = [self.box_1, self.box_2, self.box_3, self.box_4, self.box_5, self.box_6,
                      self.box_7]
        for i in range(len(listWidget)):
            layout.addStretch(listStretch[i])
            layout.addWidget(listWidget[i])
        layout.addStretch(2)

        self._control_widget = ControlWidget(self, node, AIRFRAME, self.save_file,
                                             self._do_restart_all)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self._control_widget)

        self.setLayout(layout)

        self.show()
        margin = layout.getContentsMargins()[0]

        # ------------------создание картиночки-------------------------
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
        # ---------------------------------------------------------------

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

        global circuit_subscriber
        circuit_subscriber = VtolSubscriber(node, "uavcan.equipment.power.CircuitStatus")

    def save_file(self, temp_dist):
        name = QFileDialog.getSaveFileName(self, 'Save File', "airframe.json")
        AIRFRAME2 = {}
        for block in self.blocks:
            AIRFRAME2[block.name] = block.temp_data_fields
            AIRFRAME2[block.name]["id"] = block.id
        AIRFRAME2["_control_widget"] = temp_dist
        with open(name[0], 'w') as f:
            json.dump(AIRFRAME2, f)

    def _do_restart_all(self):
        request = uavcan.protocol.RestartNode.Request(
            magic_number=uavcan.protocol.RestartNode.Request().MAGIC_NUMBER)
        if not request_confirmation('Confirm node restart',
                                    'Do you really want to send request uavcan.protocol.RestartNode?',
                                    self):
            return

        def callback(e):
            if e is not None:
                QMessageBox.about(self, 'Response', 'Restart request response: ' + str(e.response))

        try:
            for node_id in self.nodes_id:
                self._node.request(request, node_id, callback, priority=REQUEST_PRIORITY)
        except Exception as ex:
            show_error('Node error', 'Could not send restart request', ex, self)

    def _update_combo_boxes(self):
        global check_status_update

        nodes = self._monitor.find_all(lambda _: True)
        nodes_id = list(e.node_id for e in nodes)

        if nodes_id != self.nodes_id or check_status_update:
            check_status_update = False
            self.nodes_id = nodes_id
            for block in self.blocks:
                first = block.id
                n = [*nodes_id]
                if first in n:
                    n.remove(first)
                    block.status.setText("connect")
                    block.status.setStyleSheet("color:green;")
                    block.properties_button.setEnabled(True)
                else:
                    block.status.setText("nc")
                    block.status.setStyleSheet("color:red;")
                    block.properties_button.setEnabled(False)
                    block.set_voltage('-')
                    block.set_current('-')
                    block.set_health(-1)
                    for i, sub in enumerate(block.subscriptions):
                        block.data[i + 2].setText('NC')

                block.combo_box.clear()
                block.combo_box.addItem(str(first))
                block.combo_box.addItems(str(i) for i in n)

    def _nodes_update(self):
        for block in self.blocks:
            nodes = self._monitor.find_all(lambda _: True)
            logger.debug(nodes)
            nodes_health = {k.node_id: k.status.health for k in nodes}
            block.update_data(nodes, nodes_health)
