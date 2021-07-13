import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontInfo
from PyQt5.QtWidgets import QPushButton


def make_icon_button(icon_name, tool_tip, parent, checkable=False, checked=False, on_clicked=None, text=''):
    b = QPushButton(text, parent)
    b.setFocusPolicy(Qt.NoFocus)
    if icon_name:
        b.setIcon(get_icon(icon_name))
    b.setToolTip(tool_tip)
    if checkable:
        b.setCheckable(True)
        b.setChecked(checked)
    if on_clicked:
        b.clicked.connect(on_clicked)
    return b


def get_icon(name):
    return qtawesome.icon('fa.' + name)


def get_monospace_font():
    preferred = ['Consolas', 'DejaVu Sans Mono', 'Monospace', 'Lucida Console', 'Monaco']
    for name in preferred:
        font = QFont(name)
        if QFontInfo(font).fixedPitch():
            # logger.debug('Preferred monospace font: %r', font.toString())
            return font

    font = QFont()
    font.setStyleHint(QFont().Monospace)
    font.setFamily('monospace')
    # logger.debug('Using fallback monospace font: %r', font.toString())
    return font
