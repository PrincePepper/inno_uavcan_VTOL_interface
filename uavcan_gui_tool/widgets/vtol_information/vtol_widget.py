
import os
from logging import getLogger

import uavcan
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QGroupBox, QPushButton, QHBoxLayout

logger = getLogger(__name__)


class VTOLWidget(QGroupBox):
    def __init__(self, parent, node):
        super(VTOLWidget, self).__init__(parent)

        self.parent = parent
        self._node = node

        self.setTitle('Vtol monitor')

        self._vtol_open = QPushButton('Open vtol monitor window', self)
        self._vtol_open.setFocusPolicy(Qt.NoFocus)
        self._vtol_open.clicked.connect(self._on_vtol_clicked)

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update_button)
        self._update_timer.start(500)

        self._update_button()

        layout = QHBoxLayout(self)
        layout.addWidget(self._vtol_open)
        layout.addStretch()

        self.setLayout(layout)

        self._monitor = uavcan.app.node_monitor.NodeMonitor(node)

        self.window = lambda *_: None

    def _update_button(self):
        # Syncing the GUI state
        if self._node.is_anonymous:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self._update_timer.stop()

    def _on_vtol_clicked(self):
        print("clicked", self)
        if os.path.exists('../airframe.json'):
            self.window()
        else:
            logger.error("json file not exist. Please create him, otherwise i won't work!")
