from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel

from core.setting_deploy import get_resource_path


class ExplosionLabel(QLabel):
    def __init__(self, parent, color: str, pos: QPoint, size: int, fps: int = 30):
        super().__init__(parent)
        self.frames = [
            QPixmap(get_resource_path(
                f"assets/elements/explosion/{color}/frame_{i:02d}.png")
            ).scaled(size, size)
            for i in range(60)
        ]

        self._idx = 0
        self.setPixmap(self.frames[0])
        self.setGeometry(pos.x(), pos.y(), size, size)
        self.show()
        self.raise_()

        interval = int(1000 / fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next)
        self.timer.start(interval)

    def _next(self):
        self._idx += 1
        if self._idx >= len(self.frames):
            self.timer.stop()
            self.deleteLater()
        else:
            self.setPixmap(self.frames[self._idx])
