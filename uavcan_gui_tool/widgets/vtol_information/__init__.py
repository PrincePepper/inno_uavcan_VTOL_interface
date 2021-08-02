#
#
# This software is distributed under the terms of the MIT License.
#
# Author: Sereda Semen
#

import json
from logging import getLogger

from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout

from uavcan_gui_tool.widgets import LoggerCustomColor

logger = getLogger(__name__)


# the class is responsible for checking and stabilizing the fields in the JSON file when it is read
class JsonFileValidator:
    def __init__(self, path_file_name: str):
        self.file_name = path_file_name
        self.len = 0
        self.name_node = []
        self.data_types = []
        self._open_file()
        self._test_file()

    # checking for the existence of a file, as well as reading it into a local object
    def _open_file(self):
        try:
            with open(self.file_name, 'r') as f:
                self.AIRFRAME = json.load(f)
                self.len = len(self.AIRFRAME)
                with open("../data_types", 'r') as d:
                    self.data_types = d.read().split()
        except FileNotFoundError as e:
            logger.error("For some reason the file fell: " + str(e))

    # testing the AIRFRAME object to remove errors and warn the user about them
    def _test_file(self):
        if not "_control_widget" in self.AIRFRAME.keys() \
                or not "vtol_object" in self.AIRFRAME.keys():
            logger.info(LoggerCustomColor.WARNING +
                        "Json file dont have _control_widget or vtol_object" +
                        LoggerCustomColor.ENDC)
        for i, node in enumerate(self.AIRFRAME.items()):
            if node[0] != "_control_widget" and node[0] != "vtol_object":
                self.name_node.append(node[0])
                node[1].setdefault("id", -1)
                node[1].setdefault("item", -1)
                node[1].setdefault("name", "def_name")

                popped_value = []
                for data_node in node[1]:
                    if data_node != "id" and data_node != "item" and data_node != "name":
                        if not node[1][data_node] == "":
                            split_temp_data = node[1][data_node].split()
                            if not split_temp_data[0] in self.data_types:
                                logger.info(LoggerCustomColor.WARNING +
                                            "This data type does not exist:" +
                                            "«" +
                                            str(split_temp_data[0]) +
                                            "»" +
                                            LoggerCustomColor.ENDC)
                                popped_value.append(data_node)
                        else:
                            popped_value.append(data_node)
                for delete_item in popped_value:
                    node[1].pop(delete_item)
            else:
                if node[0] == "_control_widget":
                    for j in self.name_node[:8]:
                        if j not in node[1].keys():
                            node[1].setdefault(str(j), -1)

    # check for the existence of the configuration file otherwise use the default settings
    def parse_config(self):
        config_control_widget = self.AIRFRAME.pop('_control_widget')
        vtol_type = self.AIRFRAME.pop('vtol_object')
        return self.AIRFRAME, config_control_widget, vtol_type


# method that allows you to more quickly draw elements horizontally
def make_hbox(*widgets, stretch_index=None, s=1):
    box = QHBoxLayout()
    for idx, w in enumerate(widgets):
        box.addWidget(w, 0 if stretch_index is None else stretch_index[idx])
    box.addStretch(s)
    box.setContentsMargins(0, 0, 0, 0)
    container = QWidget()
    container.setLayout(box)
    container.setContentsMargins(0, 0, 0, 0)
    return container


def make_vbox(*widgets, stretch_index=None):
    box = QVBoxLayout()
    for idx, w in enumerate(widgets):
        box.addWidget(w, 1 if idx == stretch_index else 0)
    container = QWidget()
    container.setLayout(box)
    container.setContentsMargins(0, 0, 0, 0)
    return container


# def make_vbox(*widgets, stretch_index=None, s=1, margin=False):
#     box = QVBoxLayout()
#     for idx, w in enumerate(widgets):
#         if stretch_index is not None:
#             box.addStretch(stretch_index[idx])
#         box.addWidget(w)
#     box.addStretch(s)
#     container = QWidget()
#     container.setLayout(box)
#     if margin:
#         m = int(box.getContentsMargins()[0] / 2)
#         container.setContentsMargins(m, m, m, m)
#     else:
#         container.setContentsMargins(0, 0, 0, 0)
#     box.setContentsMargins(0, 0, 0, 0)
#     return container

# node life signatures
def node_health_to_str_color(health):
    return {
        -1: ("-", "color: black"),
        0: ("OK", "color: green"),
        1: ("WARNING", "color: orange"),
        2: ("ERROR", "color: magenta"),
        3: ("CRITICAL", "color: red"),
    }.get(health)
