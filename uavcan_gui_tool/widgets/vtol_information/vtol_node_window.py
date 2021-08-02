#
#
# This software is distributed under the terms of the MIT License.
#
# Author: Semen Sereda
#
import json
from logging import getLogger

import pyuavcan_v0
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QComboBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, \
    QFileDialog, QMessageBox, QSizePolicy

from uavcan_gui_tool.widgets import request_confirmation, show_error
from uavcan_gui_tool.widgets.vtol_information import JsonFileValidator, make_hbox, node_health_to_str_color, make_vbox
from uavcan_gui_tool.widgets.vtol_information.control_widget import ControlWidget
from uavcan_gui_tool.widgets.vtol_information.vtol_subscriber import VTOLSubscriber

logger = getLogger(__name__)
REQUEST_PRIORITY = 30
check_status_update = False


class NodeBlock(QDialog):
    def __init__(self, node, show_node_window, circuit_subscriber, data_nodes):
        super().__init__()

        self.id = data_nodes['id']
        self.name = data_nodes['name']
        self.item = data_nodes['item']

        self.temp_data_fields = data_nodes
        self.show_node_window = show_node_window
        self._node = node

        self.circuit_subscriber = circuit_subscriber
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
        # self.voltage_and_current_box.hide()
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
                    # TODO: нужно переделать обработку ошибки при переподключении устройсва
                    try:
                        self.set_health(nodes_health[node_id])
                    except:
                        pass
                    if self.circuit_subscriber.has_next():
                        data_circuit = self.circuit_subscriber.next()
                        self.set_voltage(data_circuit[0].payload.voltage)
                        self.set_current(data_circuit[0].payload.current)
                    print(data)
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
            self.subscriptions.append(VTOLSubscriber(self._node, i))

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
        self.show_node_window(self.id)

    def _on_changed(self, text):
        self.id = int(text)
        global check_status_update
        check_status_update = True
        if self.circuit_subscriber.has_next():
            data = self.circuit_subscriber.next()
            node_id = data[0].source_node_id
            # if self.id == node_id:
            #     self.voltage_and_current_box.show()
        # else:
        #     self.voltage_and_current_box.hide()

    def make_widget(self):
        box = make_vbox(make_hbox(self.label, self.status),
                        make_hbox(make_vbox(*self.fields), make_vbox(*self.data)),
                        self.properties_button,
                        self.voltage_and_current_box)  # margin=True
        #
        # TODO: make a normal node styling
        #
        box.setStyleSheet("background-color: white;")
        self.widget = box


class VTOLWindow(QDialog):
    def __init__(self, parent, node, show_node_window, dynamic_node_id_allocation_widget):
        super(VTOLWindow, self).__init__(parent)
        self.setWindowTitle('VTOL information')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._node = node
        self.nodes_id = []
        self.blocks = []
        # self._node_monitor_widget = NodeMonitorWidget(self, node)
        # self._node_monitor_widget.on_info_window_requested = show_node_window
        self._dynamic_node_id_allocation_widget = dynamic_node_id_allocation_widget

        self.circuit_subscriber = VTOLSubscriber(node, "uavcan.equipment.power.CircuitStatus")

        self.AIRFRAME, self.CONFIG_CONTROL_WIDGET, self.VTOL_TYPE = JsonFileValidator(
            "../airframe.json").parse_config()
        for item in self.AIRFRAME:
            self.blocks.append(NodeBlock(node, show_node_window, self.circuit_subscriber, self.AIRFRAME[item]))

        layout = QHBoxLayout(self)

        pixmap = QPixmap('../uavcan_gui_tool/icons/vtol.jpg')
        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        layout.addWidget(lbl)

        widget2 = QWidget()
        layout2 = QVBoxLayout(self)
        aaaa = 0
        for i in self.blocks:
            layout2.addWidget(i.widget)
            aaaa = i.width().real
        widget2.setLayout(layout2)

        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(widget2)
        # TODO: колхоз
        scroll.setMinimumWidth(aaaa / 1.8)

        layout.addWidget(scroll)

        self._control_widget = ControlWidget(self, node, self.AIRFRAME, self.CONFIG_CONTROL_WIDGET,
                                             self.save_file,
                                             self._do_restart_all)
        self._control_widget.setAlignment(Qt.AlignRight)
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self._control_widget)

        self.setLayout(layout)

        self.show()

        self._monitor = pyuavcan_v0.app.node_monitor.NodeMonitor(node)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._nodes_update)
        self._status_update_timer.start(100)

        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self._update_combo_boxes)
        self._status_update_timer.start(500)

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
        AIRFRAME2["vtol_object"] = self.VTOL_TYPE
        with open(name[0], 'w') as f:
            json.dump(AIRFRAME2, f)

    def _do_restart_all(self):
        request = pyuavcan_v0.protocol.RestartNode.Request(
            magic_number=pyuavcan_v0.protocol.RestartNode.Request().MAGIC_NUMBER)
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

        nodes = self._monitor.find_all(lambda _: True)
        nodes_id = list(e.node_id for e in nodes)

        global check_status_update
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
