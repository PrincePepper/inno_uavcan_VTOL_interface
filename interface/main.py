#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import logging
import multiprocessing
import os
import sys
import tempfile

from PyQt5.QtGui import QIcon

assert sys.version[0] == '3'

from argparse import ArgumentParser
parser = ArgumentParser(description='UAVCAN GUI tool')

parser.add_argument("--debug", action='store_true', help="enable debugging")
parser.add_argument("--dsdl", help="path to custom DSDL")

args = parser.parse_args()

#
# Configuring logging before other packages are imported
#
if args.debug:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

logging.basicConfig(stream=sys.stderr, level=logging_level,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

log_file = tempfile.NamedTemporaryFile(mode='w', prefix='uavcan_gui_tool-', suffix='.log', delete=False)
file_handler = logging.FileHandler(log_file.name)
file_handler.setLevel(logging_level)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(process)d] %(levelname)-8s %(name)-25s %(message)s'))
logging.root.addHandler(file_handler)

logger = logging.getLogger(__name__.replace('__', ''))
logger.info('Spawned')

#
# Applying Windows-specific hacks
#
os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.dirname(sys.executable)  # Otherwise it fails to load on Win 10

#
# Configuring multiprocessing.
# Start method must be configured globally, and only once. Using 'spawn' ensures full compatibility with Windoze.
# We need to check first if the start mode is already configured, because this code will be re-run for every child.
#
if multiprocessing.get_start_method(True) != 'spawn':
    multiprocessing.set_start_method('spawn')

#
# Importing other stuff once the logging has been configured
#
import uavcan

from PyQt5.QtWidgets import QApplication

from version import __version__
from setup_window import run_setup_window

from widgets import show_error


NODE_NAME = 'org.uavcan.gui_tool'


def main():
    logger.info('Starting the application')
    app = QApplication(sys.argv)

    while True:
        # Asking the user to specify which interface to work with
        try:
            # iface, iface_kwargs, dsdl_directory = run_setup_window(get_app_icon(), args.dsdl)
            iface, iface_kwargs, dsdl_directory = run_setup_window(QIcon(), args.dsdl)
            if not iface:
                sys.exit(0)
        except Exception as ex:
            show_error('Fatal error', 'Could not list available interfaces', ex, blocking=True)
            sys.exit(1)

        if not dsdl_directory:
            dsdl_directory = args.dsdl

        try:
            if dsdl_directory:
                logger.info('Loading custom DSDL from %r', dsdl_directory)
                uavcan.load_dsdl(dsdl_directory)
                logger.info('Custom DSDL loaded successfully')

                # setup an environment variable for sub-processes to know where to load custom DSDL from
                os.environ['UAVCAN_CUSTOM_DSDL_PATH'] = dsdl_directory
        except Exception as ex:
            logger.exception('No DSDL loaded from %r, only standard messages will be supported', dsdl_directory)
            show_error('DSDL not loaded',
                       'Could not load DSDL definitions from %r.\n'
                       'The application will continue to work without the custom DSDL definitions.' % dsdl_directory,
                       ex, blocking=True)

        # Trying to start the node on the specified interface
        try:
            node_info = uavcan.protocol.GetNodeInfo.Response()
            node_info.name = NODE_NAME
            node_info.software_version.major = __version__[0]
            node_info.software_version.minor = __version__[1]

            node = uavcan.make_node(iface,
                                    node_info=node_info,
                                    mode=uavcan.protocol.NodeStatus().MODE_OPERATIONAL,
                                    **iface_kwargs)

            # Making sure the interface is alright
            node.spin(0.1)
        except uavcan.transport.TransferError:
            # allow unrecognized messages on startup:
            logger.warning('UAVCAN Transfer Error occurred on startup', exc_info=True)
            break
        except Exception as ex:
            logger.error('UAVCAN node init failed', exc_info=True)
            show_error('Fatal error', 'Could not initialize UAVCAN node', ex, blocking=True)
        else:
            break

    logger.info('Creating main window; iface %r', iface)
    # window = MainWindow(node, iface)
    # window.show()

    # try:
    #     update_checker.begin_async_check(window)
    # except Exception:
    #     logger.error('Could not start update checker', exc_info=True)

    logger.info('Init complete, invoking the Qt event loop')
    # exit_code = app.exec_()

    node.close()

    # sys.exit(exit_code)


if __name__ == '__main__':
    main()

