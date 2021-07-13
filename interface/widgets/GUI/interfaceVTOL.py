import logging
import os
import sys

import pkg_resources
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QFontInfo, QIntValidator
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__.replace('__', ''))
logger.info('Spawned')
RUNNING_ON_LINUX = 'linux' in sys.platform.lower()

STANDARD_BAUD_RATES = 9600, 115200, 460800, 921600, 1000000, 3000000
DEFAULT_BAUD_RATE = 115200
assert DEFAULT_BAUD_RATE in STANDARD_BAUD_RATES


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI(icon=get_app_icon())
        self.on_ok()

    def initUI(self, icon):
        self.win = QDialog()
        # win.resize(1200, 600)
        self.win.setWindowIcon(icon)
        self.win.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.win.setWindowTitle('Application setup')
        self.win.setAttribute(Qt.WA_DeleteOnClose)  # This is required to stop background timers!

        self.combo = QComboBox(self.win)
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.NoInsert)
        self.combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo.setFont(get_monospace_font())

        comboCompleter = QCompleter()
        comboCompleter.setCaseSensitivity(Qt.CaseSensitive)
        comboCompleter.setModel(self.combo.model())
        self.combo.setCompleter(comboCompleter)

        self.bitrate = QSpinBox(self.win)
        self.bitrate.setMaximum(1000000)
        self.bitrate.setMinimum(10000)
        self.bitrate.setValue(1000000)

        self.baudrate = QComboBox(self.win)
        self.baudrate.setEditable(True)
        self.baudrate.setInsertPolicy(QComboBox.NoInsert)
        self.baudrate.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.baudrate.setFont(get_monospace_font())

        baudrateCompleter = QCompleter(self.win)
        baudrateCompleter.setModel(self.baudrate.model())
        self.baudrate.setCompleter(baudrateCompleter)

        self.baudrate.setValidator(QIntValidator(min(STANDARD_BAUD_RATES), max(STANDARD_BAUD_RATES)))
        self.baudrate.insertItems(0, map(str, STANDARD_BAUD_RATES))
        self.baudrate.setCurrentText(str(DEFAULT_BAUD_RATE))

        ok = QPushButton('OK', self.win)

        ok.clicked.connect(self.on_ok)

        can_group = QGroupBox('CAN interface setup', self.win)
        can_layout = QVBoxLayout()
        can_layout.addWidget(QLabel('Select CAN interface'))
        can_layout.addWidget(self.combo)

        slcan_group = QGroupBox('SLCAN adapter settings', self.win)
        slcan_layout = QGridLayout()
        slcan_layout.addWidget(QLabel('CAN bus bit rate:'), 0, 0)
        slcan_layout.addWidget(self.bitrate, 0, 1)
        slcan_layout.addWidget(QLabel('Adapter baud rate (not applicable to USB-CAN adapters):'), 1, 0)
        slcan_layout.addWidget(self.baudrate, 1, 1)
        slcan_group.setLayout(slcan_layout)

        can_layout.addWidget(slcan_group)
        can_group.setLayout(can_layout)

        layout = QVBoxLayout()
        layout.addWidget(can_group)
        layout.addWidget(ok)
        layout.setSizeConstraint(layout.SetFixedSize)
        self.win.setLayout(layout)

        def update_slcan_options_visibility():
            if RUNNING_ON_LINUX:
                slcan_active = '/' in self.combo.currentText()
            else:
                slcan_active = True
            slcan_group.setEnabled(slcan_active)

        self.combo.currentTextChanged.connect(update_slcan_options_visibility)

        # with BackgroundIfaceListUpdater() as iface_lister:
        #     update_slcan_options_visibility()
        #     update_iface_list()
        #     timer = QTimer(self.win)
        #     timer.setSingleShot(False)
        #     timer.timeout.connect(update_iface_list)
        #     timer.start(int(BackgroundIfaceListUpdater.UPDATE_INTERVAL / 2 * 1000))
        #     self.win.exec()

        self.win.exec()


def get_app_icon():
    global _APP_ICON_OBJECT
    try:
        return _APP_ICON_OBJECT
    except NameError:
        pass
    # noinspection PyBroadException
    try:
        fn = pkg_resources.resource_filename(__name__, os.path.join('res', 'icons', 'logo_256x256.png'))
        _APP_ICON_OBJECT = QtGui.QIcon(fn)

    except Exception:
        logger.error('Could not load icons', exc_info=True)
        _APP_ICON_OBJECT = QIcon()
    return _APP_ICON_OBJECT


def get_monospace_font():
    preferred = ['Consolas', 'DejaVu Sans Mono', 'Monospace', 'Lucida Console', 'Monaco']
    for name in preferred:
        font = QFont(name)
        if QFontInfo(font).fixedPitch():
            logger.debug('Preferred monospace font: %r', font.toString())
            return font

    font = QFont()
    font.setStyleHint(QFont().Monospace)
    font.setFamily('monospace')
    logger.debug('Using fallback monospace font: %r', font.toString())
    return font


def show_error(title, text, informative_text, parent=None, blocking=False):
    mbox = QMessageBox(parent)

    mbox.setWindowTitle(str(title))
    mbox.setText(str(text))
    if informative_text:
        mbox.setInformativeText(str(informative_text))

    mbox.setIcon(QMessageBox.Critical)
    mbox.setStandardButtons(QMessageBox.Ok)

    if blocking:
        mbox.exec()
    else:
        mbox.show()  # Not exec() because we don't want it to block!


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    # ex.move(int(GetSystemMetrics(0) / 2), int(GetSystemMetrics(1) / 2))
    sys.exit(app.exec_())
