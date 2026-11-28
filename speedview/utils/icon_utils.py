import os
import sys
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt


def _resource_roots():
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(os.path.join(meipass, "speedview", "ui", "resources"))
        roots.append(os.path.join(meipass, "resources"))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        roots.append(os.path.join(exe_dir, "_internal", "speedview", "ui", "resources"))
        roots.append(os.path.join(exe_dir, "speedview", "ui", "resources"))
    roots.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "resources")))
    return roots


def get_resource_path(filename):
    for root in _resource_roots():
        candidate = os.path.join(root, filename)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(_resource_roots()[-1], filename)


def get_png_icon_path():
    return get_resource_path("speedview.png")


def get_ico_path():
    return get_resource_path("speedview.ico")


def get_svg_icon_path():
    return get_resource_path("speedview_icon.svg")


def get_app_icon():
    """Build a crisp QIcon from bundled PNG/ICO or render fallback from speedview_icon.svg."""
    icon = QIcon()
    png_path = get_png_icon_path()
    if os.path.exists(png_path):
        icon.addFile(png_path)
    ico_path = get_ico_path()
    if os.path.exists(ico_path):
        icon.addFile(ico_path)
    if not icon.isNull():
        return icon

    svg_path = get_svg_icon_path()
    if os.path.exists(svg_path):
        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            pixmap = QPixmap(128, 128)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            icon.addPixmap(pixmap)
    return icon
