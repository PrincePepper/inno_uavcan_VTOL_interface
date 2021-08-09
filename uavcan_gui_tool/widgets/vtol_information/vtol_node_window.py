#
#
# This software is distributed under the terms of the MIT License.
#
# Author: Semen Sereda
#
import json
import os
from functools import partial
from logging import getLogger

import pyuavcan_v0
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QComboBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, \
    QFileDialog, QMessageBox, QSlider, QSpinBox, QStyle, QProxyStyle

from uavcan_gui_tool.widgets import request_confirmation, show_error, make_icon_button
from uavcan_gui_tool.widgets.vtol_information import JsonFileValidator, make_hbox, node_health_to_str_color, make_vbox
from uavcan_gui_tool.widgets.vtol_information.vtol_subscriber import VTOLSubscriber

__all__ = 'PANEL_NAME', 'FILE_PATCH'
PANEL_NAME = 'Vtol node panel'
FILE_PATCH = '../airframe.json'

DEFAULT_INTERVAL = 0.1

logger = getLogger(__name__)
REQUEST_PRIORITY = 30
check_status_update = False


class SliderProxyStyle(QProxyStyle):
    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_SliderThickness:
            return 100
        elif metric == QStyle.PM_SliderLength:
            return 70
        return super().pixelMetric(metric, option, widget)


class PercentSlider(QWidget):
    def __init__(self, parent):
        super(PercentSlider, self).__init__(parent)

        self._slider = QSlider(Qt.Vertical, self)
        self._slider.setMinimum(-1)
        self._slider.setMaximum(100)
        self._slider.setValue(-1)
        self._slider.setTickInterval(100)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        self._slider.showMaximized()
        # TODO: надо тестить
        self._slider.setMinimumHeight(150)
        style = SliderProxyStyle(self._slider.style())
        self._slider.setStyle(style)

        self._slider.valueChanged.connect(lambda: self._spinbox.setValue(self._slider.value()))
        self._spinbox = QSpinBox(self)
        self._spinbox.setMinimum(-1)
        self._spinbox.setMaximum(100)
        self._spinbox.setValue(-1)
        self._spinbox.valueChanged.connect(lambda: self._slider.setValue(self._spinbox.value()))

        self._zero_button = make_icon_button('hand-stop-o', 'Zero setpoint', self, on_clicked=self.zero)

        self._label = QLabel("-1", self)

        layout = QVBoxLayout(self)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(self._slider)
        sub_layout.addStretch()
        layout.addLayout(sub_layout)
        layout.addWidget(self._spinbox)
        layout.addWidget(self._zero_button)
        layout.addWidget(self._label)
        self.setLayout(layout)

    def zero(self):
        self._slider.setValue(-1)

    def get_value(self):
        return self._slider.value()

    def set_value(self, val):
        self._slider.setValue(val)

    def set_value_lbl(self, val):
        self._label.setText(str("{:1.2f}".format(val)))


class NodeBlock(QDialog):
    def __init__(self, node, show_node_window, circuit_subscriber, number_item, data_nodes):
        super().__init__()

        self.id = data_nodes['id']
        self.name = data_nodes['name']
        self.item = number_item

        self.have_channel = data_nodes.get('channels') if data_nodes.get('channels') else None

        self.have_params = data_nodes.get('params') if data_nodes.get('params') else None

        self.temp_data_fields = data_nodes['fields']
        self.show_node_window = show_node_window
        self._node = node

        self.circuit_subscriber = circuit_subscriber

        # lists for our output
        self.subscriptions = []
        self.to_subscribe = []
        self.to_subscribe_parametr = []

        self.label_item = QLabel(str(self.item), self)
        self.label_item.setStyleSheet("QLabel {"
                                      "border-style: solid;"
                                      "border-width: 3px;"
                                      "border-color: black; "
                                      "}")

        self.name_lbl = QLabel(self.name, self)
        self.status_lbl = QLabel("-", self)
        self.health_lbl = QLabel('Health:', self)
        self.health_status_lbl = QLabel('0', self)
        self.id_lbl = QLabel('id:', self)
        self.id_status_lbl = QLabel('0', self)

        self.combo_box = QComboBox(self)
        self.combo_box.activated[str].connect(self._on_changed)
        # get the name of the fields and what it stores
        self.fields, self.data = self.parse_fields(data_nodes['fields'])

        self.set_subscribe()

        self.properties_button = QPushButton('Properties', self)
        self.properties_button.setFocusPolicy(Qt.NoFocus)
        self.properties_button.clicked.connect(self.on_clicked)
        self.properties_button.setEnabled(False)

        self.slider = PercentSlider(self)
        self.voltage_lbl = QLabel('-', self)
        self.current_lbl = QLabel('-', self)

        self.widget = None

        self.combo_box.addItem(str(self.id))

        self.make_widget()
        self.ImportDataMotor()

    def parse_fields(self, fields):
        list_fields = []
        list_data = []

        # all nodes have status bar and id
        for item in fields:
            if item:
                split_temp_data_fields = item.split()
                list_fields.append(QLabel(str(split_temp_data_fields[0]), self))
                list_data.append(QLabel("0", self))
                self.to_subscribe.append(split_temp_data_fields[1])
                self.to_subscribe_parametr.append(split_temp_data_fields[2])

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
                    # print(data)
                    self.data[i].setText(
                        str("{:1.2f}".format(
                            eval(f"data[0].payload.{self.to_subscribe_parametr[i]}"))))

            else:
                # if the data type does not match the given id, then it will report it
                global check_status_update
                if check_status_update:
                    self.data[i].setText('error')

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
        self.health_status_lbl.setText(text)
        self.health_status_lbl.setStyleSheet(style)

    def on_clicked(self):
        self.show_node_window(self.id)

    def _on_changed(self, text):
        self.id = int(text)
        global check_status_update
        check_status_update = True

    def dsdasdsad(self):
        if self.have_params:
            index_params = []
            for j, i in enumerate(self._params):
                if "mode" in str(i.name) or "_def" in str(i.name) or "_max" in str(i.name) or "_min" in str(i.name):
                    index_params.append(j)
            for i, item in enumerate(index_params):
                for j in self.have_params:
                    temp_item = j.split()
                    if temp_item[0] == self._params[item].name:
                        self._param_struct = self._params[item]
                        self._param_struct.value.integer_value = int(temp_item[1])
                        request = pyuavcan_v0.protocol.param.GetSet.Request(name=self._param_struct.name,
                                                                            value=self._param_struct.value)
                        logger.info('Sending param set request: %s', request)
                        self._node.request(request, self.id, self._on_response, priority=30)

    def _on_response(self, e):
        if e is None:
            logger.info('Request timed out')
        else:
            logger.info('Param get/set response: %s', e.response)
            logger.info('Response received')

    def ImportDataMotor(self):
        try:
            if self.id == -1:
                return
            index = 0
            self._node.request(pyuavcan_v0.protocol.param.GetSet.Request(index=index),
                               self.id,
                               partial(self._on_fetch_response, index),
                               priority=31)
        except Exception as ex:
            logger.error('Node error', 'Could not send param get request', ex, self)
        else:
            logger.info('Param fetch request sent')
            self._params = []

    def _on_fetch_response(self, index, e):
        if e is None:
            logger.error('Param fetch failed: request timed out')
            return
        if len(e.response.name) == 0:
            logger.info('%d params fetched successfully', index)
            self.dsdasdsad()
            return

        self._params.append(e.response)

        try:
            index += 1
            self._node.defer(0.1, lambda: self._node.request(
                pyuavcan_v0.protocol.param.GetSet.Request(index=index),
                self.id,
                partial(self._on_fetch_response, index),
                priority=31))
        except Exception as ex:
            logger.error('Param fetch error', exc_info=True)

    def make_widget(self):

        self.voltage_and_current_box = make_hbox(self.voltage_lbl, self.current_lbl, stretch_index=[1, 0], s=1)

        box = make_hbox(
            make_vbox(make_hbox(self.label_item, self.name_lbl, self.status_lbl, stretch_index=[0, 1, 0], s=1),
                      make_hbox(self.health_lbl, self.health_status_lbl, self.id_lbl, self.combo_box),
                      make_hbox(make_vbox(*self.fields), make_vbox(*self.data)),
                      make_hbox(self.properties_button),
                      self.voltage_and_current_box),
            self.slider if self.have_channel else None, stretch_index=[1, 1], s=1)  # margin=True
        #
        # TODO: make a normal node styling
        #
        box.setStyleSheet("background-color: white;")
        # print(box.height())
        self.widget = box
        self.widget.setMinimumHeight(self.widget.height())
        self.widget.setMinimumWidth(self.widget.width())
        self.widget.resize(self.minimumWidth(), self.minimumHeight())


class VTOLWindow(QDialog):
    CMD_BIT_LENGTH = pyuavcan_v0.get_uavcan_data_type(pyuavcan_v0.equipment.esc.RawCommand().cmd).value_type.bitlen
    CMD_MAX = 2 ** (CMD_BIT_LENGTH - 1) - 1
    CMD_MIN = 0

    def __init__(self, parent, node, show_node_window, dynamic_node_id_allocation_widget):
        super(VTOLWindow, self).__init__(parent)
        self.setWindowTitle('VTOL information')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._node = node
        self.nodes_id = []
        self.blocks = []
        self._dynamic_node_id_allocation_widget = dynamic_node_id_allocation_widget

        self.circuit_subscriber = VTOLSubscriber(node, "uavcan.equipment.power.CircuitStatus")

        if not os.path.exists(FILE_PATCH):
            logger.error("Json config not exist")
            return
        self.AIRFRAME, self.VTOL_TYPE = JsonFileValidator(FILE_PATCH).parse_config()
        for i, item in enumerate(self.AIRFRAME):
            self.blocks.append(NodeBlock(node, show_node_window, self.circuit_subscriber, i, self.AIRFRAME[item]))

        layout = QHBoxLayout(self)

        pixmap = QPixmap
        if self.VTOL_TYPE == 1:
            pixmap = QPixmap('../uavcan_gui_tool/icons/vtol.jpg')
        else:
            if self.VTOL_TYPE == 2:
                pixmap = QPixmap('../uavcan_gui_tool/icons/logo_256x256.png')

        from screeninfo import get_monitors
        for m in get_monitors():
            pixmap = pixmap.scaled(m.width * 0.65, m.height * 0.65, Qt.KeepAspectRatio)

        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        layout.addWidget(lbl)

        widget2 = QWidget()
        layout2 = QVBoxLayout(self)
        for i in self.blocks:
            layout2.addWidget(i.widget)
        widget2.setLayout(layout2)

        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.resize(widget2.width(), widget2.minimumHeight())
        scroll.setMinimumWidth(widget2.width())
        scroll.setWidget(widget2)

        layout.addWidget(scroll)

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

        self._bcast_timer = QTimer(self)
        self._bcast_timer.start(DEFAULT_INTERVAL * 1e3)
        self._bcast_timer.timeout.connect(self._do_broadcast)

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

    def _do_broadcast(self):
        try:
            msg = pyuavcan_v0.equipment.esc.RawCommand()
            temp_msg = [0] * len(self.blocks)
            for sl in self.blocks:
                if sl.have_channel is not None:
                    raw_value = sl.slider.get_value() / 100
                    value = (self.CMD_MIN if raw_value < 0 else self.CMD_MAX) * raw_value
                    temp_msg[int(sl.have_channel[1:-1])] = int(value)
                    sl.slider.set_value_lbl(value)
            # print(temp_msg)
            for item in temp_msg:
                msg.cmd.append(item)
            self._node.broadcast(msg)
        except Exception as ex:
            logger.error('Publishing failed:\n' + str(ex))

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
                    block.status_lbl.setText("connect")
                    block.status_lbl.setStyleSheet("color:green;")
                    block.properties_button.setEnabled(True)
                else:
                    block.status_lbl.setText("nc")
                    block.status_lbl.setStyleSheet("color:red;")
                    block.properties_button.setEnabled(False)
                    block.set_voltage('-')
                    block.set_current('-')
                    block.set_health(-1)
                    for i, sub in enumerate(block.subscriptions):
                        block.data[i].setText('NC')

                block.combo_box.clear()
                block.combo_box.addItem(str(first))
                block.combo_box.addItems(str(i) for i in n)

    def _nodes_update(self):
        for block in self.blocks:
            nodes = self._monitor.find_all(lambda _: True)
            logger.debug(nodes)
            nodes_health = {k.node_id: k.status.health for k in nodes}
            block.update_data(nodes, nodes_health)
