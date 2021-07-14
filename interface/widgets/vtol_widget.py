#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import uavcan
from PyQt5.QtWidgets import QGroupBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from logging import getLogger

logger = getLogger(__name__)


class VtolWidget(QGroupBox):
    def __init__(self, parent, node):
        super(VtolWidget, self).__init__(parent)

        self.parent = parent
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

        # self._nodes_timer = QTimer(self)
        # self._nodes_timer.setSingleShot(False)
        # self._nodes_timer.timeout.connect(self._nodes_print)

        self._update_button()

        layout = QHBoxLayout(self)
        layout.addWidget(self._vtol_open)
        layout.addStretch(1)

        self.setLayout(layout)

        self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

        self.window = lambda *_: None

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
        try:
            self.window()
        except Exception as e:
            logger.info(e)
        # self._nodes_timer.start(1000)

