import logging
import queue

import uavcan
from PyQt5.QtWidgets import QDialog

from .active_data_type_detector import ActiveDataTypeDetector

logger = logging.getLogger(__name__)


# class QuantityDisplay(QWidget):
#     def __init__(self, parent, quantity_name, units_of_measurement):
#         super(QuantityDisplay, self).__init__(parent)
#
#         self._label = QLabel('?', self)
#
#         layout = QHBoxLayout(self)
#         layout.addStretch(1)
#         layout.addWidget(QLabel(quantity_name, self))
#         layout.addWidget(self._label)
#         layout.addWidget(QLabel(units_of_measurement, self))
#         layout.addStretch(1)
#         layout.setContentsMargins(0, 0, 0, 0)
#         self.setLayout(layout)
#
#     def set(self, value):
#         self._label.setText(str(value))


# class RateEstimator:
#     def __init__(self, update_interval=0.5, averaging_period=4):
#         self._update_interval = update_interval
#         self._estimate_lifetime = update_interval * averaging_period
#         self._averaging_period = averaging_period
#         self._hist = []
#         self._checkpoint_ts = 0
#         self._events_since_checkpoint = 0
#         self._estimate_expires_at = time.monotonic()
#
#     def register_event(self, timestamp):
#         self._events_since_checkpoint += 1
#
#         dt = timestamp - self._checkpoint_ts
#         if dt >= self._update_interval:
#            # Resetting the stat if expired
#             mono_ts = time.monotonic()
#             expired = mono_ts > self._estimate_expires_at
#             self._estimate_expires_at = mono_ts + self._estimate_lifetime
#             if expired:
#                 self._hist = []
#             elif len(self._hist) >= self._averaging_period:
#                 self._hist.pop()
#            # Updating the history
#             self._hist.insert(0, self._events_since_checkpoint / dt)
#             self._checkpoint_ts = timestamp
#             self._events_since_checkpoint = 0

#        def get_rate_with_timestamp(self):
#             if time.monotonic() <= self._estimate_expires_at:
#                 return (sum(self._hist) / len(self._hist)), self._checkpoint_ts


class VtolSubscriber(QDialog):
    # WINDOW_NAME_PREFIX = 'Subscriber'

    def __init__(self, node, type: str):
        super(VtolSubscriber, self).__init__()
        # self.setWindowTitle(self.WINDOW_NAME_PREFIX)
        # self.setAttribute(Qt.WA_DeleteOnClose)              # This is required to stop background timers!

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
        # Global statistics
        # self._num_messages_total += 1

        # Rendering and filtering
        try:
            # text = uavcan.to_yaml(e)
            text = e.transfer
            # if not self._apply_filter(text):
            #     return
        except Exception as ex:
            self._num_errors += 1
            text = '!!! [%d] MESSAGE PROCESSING FAILED: %s' % (self._num_errors, ex)
        # else:
        #     self._num_messages_past_filter += 1
        #     self._msgs_per_sec_estimator.register_event(e.transfer.ts_monotonic)

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
            # selected_type = self._type_selector.currentText().strip()
            # if not selected_type:
            #     return
            data_type = uavcan.TYPENAMES[selected_type]
        except Exception as ex:
            logger.info('Subscription error', 'Could not load requested data type', ex, self)
            return

        try:
            self._subscriber_handle = self._node.add_handler(data_type, self._on_message)
        except Exception as ex:
            logger.info('Subscription error', 'Could not create requested subscription', ex, self)
            return

        # self.setWindowTitle('%s [%s]' % (self.WINDOW_NAME_PREFIX, selected_type))
        # self._start_stop_button.setChecked(True)

    # def _do_redraw(self):
    #     self._num_messages_total_label.set(self._num_messages_total)
    #     self._num_messages_past_filter_label.set(self._num_messages_past_filter)
    #
    #     estimated_rate = self._msgs_per_sec_estimator.get_rate_with_timestamp()
    #     self._msgs_per_sec_label.set('N/A' if estimated_rate is None else ('%.0f' % estimated_rate[0]))
    #
    #     if self._pause_button.isChecked():
    #         return
    #
    #     self._log_viewer.setUpdatesEnabled(False)
    #     while True:
    #         try:
    #             text = self._message_queue.get_nowait()
    #         except queue.Empty:
    #             break
    #         else:
    #             self._log_viewer.appendPlainText(text + '\n')
    #
    #     self._log_viewer.setUpdatesEnabled(True)

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
        # self._log_viewer.setUpdatesEnabled(True)

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
        # self._type_selector.clear()
        # self._type_selector.addItems(items)

    # def _do_clear(self):
    #     self._num_messages_total = 0
    #     self._num_messages_past_filter = 0
    #     self._do_redraw()
    #     self._log_viewer.clear()

    def closeEvent(self, qcloseevent):
        try:
            self._subscriber_handle.close()
        except Exception:
            pass
        super(VtolSubscriber, self).closeEvent(qcloseevent)

    # @staticmethod
    # def spawn(parent, node, active_data_type_detector):
    #     SubscriberWindow(parent, node, active_data_type_detector).show()
