# from PyQt5 import uic
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication
from win32api import GetSystemMetrics


class VtolWindow(QDialog):
    # def __init__(self, parent, node):

    resized = QtCore.pyqtSignal()

    def __init__(self):
        # super(VtolWindow, self).__init__(parent)
        super(VtolWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle('VTOL Info')

        self._old_height = 0
        self._old_width = 0

        # self._node = node
        # self._file_server_widget = file_server_widget

        # self._info_box = InfoBox(self, target_node_id, node_monitor)
        # self._controls = Controls(self, node, target_node_id, file_server_widget, dynamic_node_id_allocator_widget)
        # self._config_params = ConfigParams(self, node, target_node_id)

        # self._status_bar = QStatusBar(self)
        # self._status_bar.setSizeGripEnabled(False)

        self._label = QLabel(self)
        self._pixmap = QPixmap('GUI/res/icons/vtol2.jpg')
        self._pixmap = self._pixmap.scaledToWidth(int(GetSystemMetrics(0)/2))
        self._label.setPixmap(self._pixmap)

        # Optional, resize window to image size
        # self.resize(self._pixmap.width(), self._pixmap.height())

        layout = QVBoxLayout(self)
        # layout.addWidget(self._info_box)
        # layout.addWidget(self._controls)
        # layout.addWidget(self._config_params)
        layout.addWidget(self._label)

        left, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(left, top, right, bottom)

        self.setLayout(layout)

        # uic.loadUi('widgets/GUI/UI/vtol.ui', self)
        self.show()  # Show the GUI

        self.setFixedWidth(self.width())
        self.setFixedHeight(self.height())


app = QApplication(sys.argv)
window = VtolWindow()
app.exec_()

