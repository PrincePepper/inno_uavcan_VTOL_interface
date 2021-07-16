# from PyQt5 import uic
import sys

from IPython.external.qt_for_kernel import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget

from interface.widgets import get_monospace_font
from interface.widgets.vtol_control_widget import ControlWidget

SCALE = 0.4


class VtolWindow(QDialog):
    # def __init__(self, parent, node):
    def __init__(self):
        super().__init__()
        self.setObjectName("VTOL Info")
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setFont(get_monospace_font())
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.setWindowTitle('VTOL Info')
        # self.setWindowIcon(get_app_icon())

        self._control_widget = ControlWidget(self)
        self.widget_output = QWidget(self)
        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.setObjectName("mainHorizontalLayout")

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        self.setContentsMargins(0, 0, 0, 0)
        self._control_widget.setContentsMargins(0, 0, 0, 0)
        self.widget_output.setContentsMargins(0, 0, 0, 0)
        self.mainHorizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        image = QImage('GUI/res/icons/vtol2.jpg')
        h1 = image.width()
        image = image.scaledToHeight(self._control_widget.height())
        h2 = image.width()
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(image))
        self.setPalette(palette)
        # self.resize(int(1280 * h2 / h1) + self._control_widget.width(), image.height())

        # self.widget_output.setStyleSheet("background-image: url(GUI/res/icons/vtol4.jpg); background-repeat: no-repeat;")
        # self._label = QLabel(self)
        # self._pixmap = QPixmap('GUI/res/icons/vtol2.jpg')
        # self._pixmap = self._pixmap.scaledToWidth(int(GetSystemMetrics(0) / 2))
        # self._label.setPixmap(self._pixmap)
        # self.verticalLayout.addWidget(self._label)

        self.verticalLayout.addStretch(1)
        # ------------------------------------------
        self.horizontalLayoutEleron = QHBoxLayout()
        self.horizontalLayoutEleron.setObjectName("horizontalLayoutEleron")

        self.but1 = QPushButton('but1', self)
        self.but2 = QPushButton('but2', self)
        self.but2.setAutoFillBackground(True)
        self.but2.setStyleSheet("background-color: #ffffff")
        self.horizontalLayoutEleron.addStretch()
        self.horizontalLayoutEleron.addWidget(self.but1)
        self.horizontalLayoutEleron.addStretch()
        self.horizontalLayoutEleron.addWidget(self.but2)
        self.horizontalLayoutEleron.addStretch()

        self.verticalLayout.addLayout(self.horizontalLayoutEleron)
        # --------------------------------------------------------
        self.verticalLayout.addStretch(2)

        self.widget_output.setLayout(self.verticalLayout)

        self.horizontalLayout.addWidget(self.widget_output)
        self.horizontalLayout.addWidget(self._control_widget)
        self.mainHorizontalLayout.addLayout(self.horizontalLayout)

        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()


class BackPicture(QLabel):
    def __init__(self, picture, x, *args, **kwargs):
        super(BackPicture, self).__init__(*args, **kwargs)
        self.setFixedSize(x, x)
        self.x = x
        self.setPicture(picture)

    def setPicture(self, picture):
        self.setPixmap(QPixmap(picture).scaled(self.x, self.x, QtCore.Qt.KeepAspectRatio))


class ImageLabel(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(ImageLabel, self).__init__(*args, **kwargs)
        self.setScene(QGraphicsScene())
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def setImage(self, filename):
        self.setPixmap(QPixmap(filename))

    def setPixmap(self, pixmap):
        item = QGraphicsPixmapItem(pixmap)
        item.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.scene().addItem(item)

    def resizeEvent(self, event):
        r = self.scene().itemsBoundingRect()
        self.fitInView(r, QtCore.Qt.KeepAspectRatio)
        super(ImageLabel, self).resizeEvent(event)


app = QApplication(sys.argv)
# app.setStyle('Fusion')
window = VtolWindow()
app.exec_()
