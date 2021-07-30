#
# This software is distributed under the terms of the MIT License.
#
# Author: Semen Sereda and Alexander Terletsky
#
import json
import logging

import uavcan
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy, \
    QComboBox, QFileDialog, QMessageBox, QPushButton, QScrollArea

from . import request_confirmation, show_error, Bcolors
from .dynamic_node_id_allocator import DynamicNodeIDAllocatorWidget
from .file_server import FileServerWidget
from .node_monitor import NodeMonitorWidget
from .node_properties import NodePropertiesWindow
from .vtol_control_widget import ControlWidget
from .vtol_subscriber import VtolSubscriber

REQUEST_PRIORITY = 30
global node_block_properties
global AIRFRAME, CONFIG_CONTROL_WIDGET, VTOL_TYPE
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


# the class is responsible for checking and stabilizing the fields in the JSON file when it is read
class JsonFileValidator:
    def __init__(self, path_file_name: str):
        self.file_name = path_file_name
        self.len = 0
        self.name_node = []
        self.data_types = []
        self._open_file()
        self._test_file()

    # checking for the existence of a file, as well as reading it into a local object
    def _open_file(self):
        try:
            with open(self.file_name, 'r') as f:
                self.AIRFRAME = json.load(f)
                self.len = len(self.AIRFRAME)
                with open("widgets/data_types", 'r') as d:
                    self.data_types = d.read().split()
        except FileNotFoundError as e:
            logger.error("For some reason the file fell: " + str(e))

    # testing the AIRFRAME object to remove errors and warn the user about them
    def _test_file(self):
        if not "_control_widget" in self.AIRFRAME.keys() \
                or not "vtol_object" in self.AIRFRAME.keys():
            logger.info(Bcolors.WARNING +
                        "Json file dont have _control_widget or vtol_object" +
                        Bcolors.ENDC)
        for i, node in enumerate(self.AIRFRAME.items()):
            if node[0] != "_control_widget" and node[0] != "vtol_object":
                self.name_node.append(node[0])
                node[1].setdefault("id", -1)
                node[1].setdefault("item", -1)
                node[1].setdefault("name", "def_name")

                popped_value = []
                for data_node in node[1]:
                    if data_node != "id" and data_node != "item" and data_node != "name":
                        if not node[1][data_node] == "":
                            split_temp_data = node[1][data_node].split()
                            if not split_temp_data[0] in self.data_types:
                                logger.info(Bcolors.WARNING +
                                            "This data type does not exist:" + "«" +
                                            str(split_temp_data[0]) + "»" +
                                            Bcolors.ENDC)
                                popped_value.append(data_node)
                        else:
                            popped_value.append(data_node)
                for delete_item in popped_value:
                    node[1].pop(delete_item)
            else:
                if node[0] == "_control_widget":
                    for j in self.name_node[:8]:
                        if j not in node[1].keys():
                            node[1].setdefault(str(j), -1)

    # check for the existence of the configuration file otherwise use the default settings
    def parse_config(self):
        config_control_widget = self.AIRFRAME.pop('_control_widget')
        vtol_type = self.AIRFRAME.pop('vtol_object')
        return self.AIRFRAME, config_control_widget, vtol_type


class NodeBlock(QDialog):
    def __init__(self, data_nodes, config_control_widget):
        super().__init__()

        self.id = data_nodes['id']
        self.name = data_nodes['name']
        self.item = data_nodes['item']

        self.temp_data_fields = data_nodes

        global main_node
        self._node = main_node

        # lists for our output
        self.subscriptions = []
        self.to_subscribe = []
        self.to_subscribe_parametr = []

        self.label = QLabel(self.name, self)
        self.status = QLabel("", self)
        self.combo_box = QComboBox(self)
        self.combo_box.activated[str].connect(self._on_changed)
        # get the name of the fields and what it stores
        self.fields, self.data = self.parse_fields(data_nodes)

        self.set_subscribe()

        self.voltage_lbl = QLabel('-', self)
        self.current_lbl = QLabel('-', self)

        self.properties_button = QPushButton('Properties', self)
        self.properties_button.setFocusPolicy(Qt.NoFocus)
        self.properties_button.clicked.connect(self.on_clicked)
        self.properties_button.setEnabled(False)

        self.widget = None

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
        for i in fields:
            if i != "id" and i != "item" and i != "name":
                list_fields.append(QLabel(str(i), self))
                list_data.append(QLabel("0", self))
                if not fields[i] == "":
                    split_temp_data_fields = fields[i].split()
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


        global main_node
        main_node = node
        self._node = node
        self.nodes_id = []
        self.blocks = []

        self._file_server_widget = FileServerWidget(self, node)
        self._node_monitor_widget = NodeMonitorWidget(self, node)
        self._dynamic_node_id_allocation_widget = DynamicNodeIDAllocatorWidget(self, node,
                                                                               self._node_monitor_widget.monitor)
        global node_block_properties
        node_block_properties = NodeBlockProperties(node, self, self._file_server_widget,
                                                    self._node_monitor_widget,
                                                    self._dynamic_node_id_allocation_widget)
        self.setAttribute(Qt.WA_DeleteOnClose)
        global AIRFRAME, CONFIG_CONTROL_WIDGET, VTOL_TYPE
        AIRFRAME, CONFIG_CONTROL_WIDGET, VTOL_TYPE = JsonFileValidator(
            "../airframe.json").parse_config()

        for item in AIRFRAME:
            self.blocks.append(NodeBlock(AIRFRAME[item], CONFIG_CONTROL_WIDGET))

        layout = QHBoxLayout(self)

        pixmap = QPixmap('widgets/GUI/res/icons/vtol.jpg')
        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        layout.addWidget(lbl)

        widget2 = QWidget()
        layout2 = QVBoxLayout(self)
        for i in self.blocks:
            layout2.addWidget(i.widget)
        widget2.setLayout(layout2)

        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(widget2)

        layout.addWidget(scroll)

        self._control_widget = ControlWidget(self, node, AIRFRAME, CONFIG_CONTROL_WIDGET,
                                             self.save_file,
                                             self._do_restart_all)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self._control_widget)

        # self.setLayout(layout)

        self.show()

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

    #
    # TODO: требуется исправить сохранения json файла из за нового формата
    #
    def save_file(self, temp_dist):
        name = QFileDialog.getSaveFileName(self, 'Save File', "airframe.json")
        AIRFRAME2 = {}
        for block in self.blocks:
            AIRFRAME2[block.name] = block.temp_data_fields
            AIRFRAME2[block.name]["id"] = block.id
        AIRFRAME2["_control_widget"] = temp_dist
        AIRFRAME2["vtol_object"] = VTOL_TYPE
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
