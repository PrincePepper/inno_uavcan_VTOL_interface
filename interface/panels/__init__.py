#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#


# TODO: Load all inner modules automatically. This is not really easy because we have to support freezing.

from PyQt5.QtWidgets import QMessageBox

from . import esc_panel
from . import actuator_panel
from . import functions


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
        mbox.show()     # Not exec() because we don't want it to block!


class PanelDescriptor:
    def __init__(self, module):
        self.name = module.PANEL_NAME
        self._module = module

    def get_icon(self):
        # noinspection PyBroadException
        try:
            return self._module.get_icon()
        except Exception:
            pass

    def safe_spawn(self, parent, node):
        try:
            return self._module.spawn(parent, node)
        except Exception as ex:
            show_error('Panel error', 'Could not spawn panel', ex)


PANELS = sorted([
    PanelDescriptor(esc_panel),
    PanelDescriptor(actuator_panel)
], key=lambda x: x.name)
