import logging
import queue

import pyuavcan_v0
from PyQt5.QtWidgets import QDialog

from uavcan_gui_tool.active_data_type_detector import ActiveDataTypeDetector

logger = logging.getLogger(__name__)


class VTOLSubscriber(QDialog):

    def __init__(self, node, type: str):
        super(VTOLSubscriber, self).__init__()

        self._node = node
        self._active_data_type_detector = ActiveDataTypeDetector(node)
        self._active_data_type_detector.message_types_updated.connect(self._update_data_type_list)

        self._message_queue = queue.Queue()

        self._subscriber_handle = None
        self._num_errors = 0

        # Initial updates
        self._update_data_type_list(True)
        self._update_data_type_list(False)

        self._do_start(type)

    def _on_message(self, e):
        # Rendering and filtering
        try:
            # text = uavcan.to_yaml(e)
            text = e.transfer
            # if not self._apply_filter(text):
            #     return
        except Exception as ex:
            self._num_errors += 1
            text = '!!! [%d] MESSAGE PROCESSING FAILED: %s' % (self._num_errors, ex)

        # Sending the text for later rendering
        try:
            self._message_queue.put_nowait(text)
        except queue.Full:
            pass

    def _do_stop(self):
        if self._subscriber_handle is not None:
            self._subscriber_handle.remove()
            self._subscriber_handle = None

        # self._pause_button.setChecked(False)
        # self.setWindowTitle(self.WINDOW_NAME_PREFIX)

    def _do_start(self, selected_type):
        self._do_stop()
        # self._do_clear()

        try:
            data_type = pyuavcan_v0.TYPENAMES[selected_type]
        except Exception as ex:
            logger.info('Subscription error', 'Could not load requested data type', ex, self)
            return

        try:
            self._subscriber_handle = self._node.add_handler(data_type, self._on_message)
        except Exception as ex:
            logger.info('Subscription error', 'Could not create requested subscription', ex, self)
            return

    def has_next(self):
        return self._message_queue.qsize() > 0

    def next(self):
        return self._message_queue.get_nowait(), self._message_queue.qsize()

    def _do_print(self):
        while True:
            try:
                text = self._message_queue.get_nowait()
            except queue.Empty:
                break
            else:
                print(text)

    def _update_data_type_list(self, a=False):
        # logger.info('Updating data type list')
        try:
            if a:
                items = self._active_data_type_detector.get_names_of_all_message_types_with_data_type_id()
            else:
                items = self._active_data_type_detector.get_names_of_active_messages()
            # print("items:", items)
        except Exception as e:
            print(e)

    def closeEvent(self, qcloseevent):
        try:
            self._subscriber_handle.close()
        except Exception:
            pass
        super(VTOLSubscriber, self).closeEvent(qcloseevent)
