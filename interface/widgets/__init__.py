from logging import getLogger
from PyQt5.QtGui import QIcon, QFont, QFontInfo
from PyQt5.QtWidgets import QMessageBox


logger = getLogger(__name__)


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


# def get_app_icon():
#     global _APP_ICON_OBJECT
#     try:
#         return _APP_ICON_OBJECT
#     except NameError:
#         pass
#     # noinspection PyBroadException
#     try:
#         fn = pkg_resources.resource_filename('interface', os.path.join('icons', 'logo_256x256.png'))
#         _APP_ICON_OBJECT = QIcon(fn)
#     except Exception:
#         logger.error('Could not load icon', exc_info=True)
#         _APP_ICON_OBJECT = QIcon()
#     return _APP_ICON_OBJECT

