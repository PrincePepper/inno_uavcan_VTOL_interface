#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import uavcan
from PyQt5.QtWidgets import QGroupBox, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from logging import getLogger

logger = getLogger(__name__)

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


class VtolWidget(QGroupBox):
    def __init__(self, parent, node):
        super(VtolWidget, self).__init__(parent)

        self._node = node
        # self._node_id_collector = uavcan.app.message_collector.MessageCollector(
        #     self._node, uavcan.protocol.NodeStatus, timeout=uavcan.protocol.NodeStatus().OFFLINE_TIMEOUT_MS * 1e-3)

        self.setTitle('Vtol monitor')

        self._vtol_open = QPushButton('Open vtol monitor window', self)
        self._vtol_open.setFocusPolicy(Qt.NoFocus)
        self._vtol_open.clicked.connect(self._on_vtol_clicked)

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update_button)
        self._update_timer.start(500)

        self._nodes_timer = QTimer(self)
        self._nodes_timer.setSingleShot(False)
        self._nodes_timer.timeout.connect(self._nodes_print)

        self._update_button()

        layout = QHBoxLayout(self)
        layout.addWidget(self._vtol_open)
        layout.addStretch(1)

        self.setLayout(layout)

        self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

    # def close(self):
    #     self._node_id_collector.close()

    def _update_button(self):
        # Syncing the GUI state
        if self._node.is_anonymous:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self._update_timer.stop()

    def _on_vtol_clicked(self):
        print("clicked", self)
        self._nodes_timer.start(1000)

    def _nodes_print(self):
        nodes = list(self._monitor.find_all(lambda _: True))
        print("Nodes:")
        for e in nodes:
            print("NID:", e.node_id)
            print("Name", e.info.name if e.info else '?')
            print("Mode", e.status.mode)
            print("Health", e.status.health)
            print("Uptime", e.status.uptime_sec)
            print("VSSC", render_vendor_specific_status_code(e.status.vendor_specific_status_code))
        print()
