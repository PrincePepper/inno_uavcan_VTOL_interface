# from PyQt5 import uic
import sys

from IPython.external.qt_for_kernel import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QSizePolicy

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
        self._control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.setObjectName("mainHorizontalLayout")

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        # self.widget_output = QWidget(self)
        # image = QImage('GUI/res/icons/vtol3.jpg')
        # palette = QPalette()
        # palette.setBrush(QPalette.Window, QBrush(image))
        # # palette.setBrush(QPalette.Background, QBrush(QPixmap("GUI/res/icons/vtol3.jpg")))
        # self.widget_output.setPalette(palette)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        self.verticalLayout.addStretch(1)

        # ------------------------------------------
        self.horizontalLayoutEleron = QHBoxLayout()
        self.horizontalLayoutEleron.setObjectName("horizontalLayoutEleron")

        self.but1 = QPushButton('but1', self)
        self.but2 = QPushButton('but2', self)

        self.horizontalLayoutEleron.addStretch(1)
        self.horizontalLayoutEleron.addWidget(self.but1)
        self.horizontalLayoutEleron.addStretch(1)
        self.horizontalLayoutEleron.addWidget(self.but2)
        self.horizontalLayoutEleron.addStretch(1)

        self.verticalLayout.addLayout(self.horizontalLayoutEleron)
        # --------------------------------------------------------

        self.verticalLayout.addStretch(2)

        # self.widget_output.setLayout(self.verticalLayout)

        # self.aaa = ImageLabel()
        # self.aaa.setImage("GUI/res/icons/vtol3.jpg")
        # self.horizontalLayout.addWidget(self.aaa)
        self.horizontalLayout.addLayout(self.verticalLayout)

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
