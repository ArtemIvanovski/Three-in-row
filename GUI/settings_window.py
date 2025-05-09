from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from PyQt5.QtGui import QPixmap, QIcon, QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QGraphicsOpacityEffect
)

from core.setting_deploy import get_resource_path


class SettingsWindow(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowOpacity(0.0)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(340, 340)
        self.sound_on = True
        self.music_on = True

        title = QLabel(self)
        title.setPixmap(
            QPixmap(get_resource_path("assets/setting_title.png"))
            .scaled(250, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        title.setGeometry(40, 0, 250, 80)

        font_id = QFontDatabase.addApplicationFont(get_resource_path("assets/FontFont.otf"))
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = families[0] if families else self.font().family()

        lbl = QLabel('Настройки', self)
        lbl.setFont(QFont(self.font_family, 18))
        lbl.setStyleSheet("color: rgb(230,230,40);")
        lbl.setGeometry(85, 9, 200, 50)
        lbl.raise_()

        bg = QLabel(self)
        bg.setStyleSheet("background: rgb(255, 204, 141); border:6px solid #af5829; border-radius:30px;")
        bg.setGeometry(0, 40, 320, 300)
        bg.lower()

        close_btn = QPushButton(self)
        close_btn.setIcon(QIcon(get_resource_path("assets/buttons/cancel.png")))
        close_btn.setIconSize(QSize(60, 60))
        close_btn.setFlat(True)
        close_btn.setGeometry(280, 20, 60, 60)
        close_btn.clicked.connect(self.close)

        self.home_btn = QPushButton(self)
        self.home_btn.setIcon(QIcon(get_resource_path("assets/buttons/home.png")))
        self.home_btn.setIconSize(QSize(80, 80))
        self.home_btn.setFlat(True)
        self.home_btn.setGeometry(210, 155, 80, 80)
        self.home_btn.clicked.connect(self.close)

        self.sound_on = True
        self.sound_btn = self._make_icon_button("sound", 24, 155)
        self.sound_btn.clicked.connect(self._toggle_sound)

        self.music_on = True
        self.music_btn = self._make_icon_button("music", 117, 155)
        self.music_btn.clicked.connect(self._toggle_music)

    def _make_icon_button(self, name: str, x: int, y: int) -> QPushButton:
        btn = QPushButton(self)
        btn.setIcon(QIcon(get_resource_path(f"assets/buttons/{name}.png")))
        btn.setIconSize(QSize(80, 80))
        btn.setFlat(True)
        btn.setGeometry(x, y, 80, 80)

        off = QLabel(btn)
        off.setPixmap(QPixmap(get_resource_path("assets/buttons/off.png")).scaled(80, 80))
        off.setAlignment(Qt.AlignCenter)
        off.hide()
        btn._off = off
        return btn

    # -------------------------------------------------------------------------
    def _toggle_sound(self):
        self.sound_on = not self.sound_on
        self.sound_btn._off.setVisible(not self.sound_on)

    def _toggle_music(self):
        self.music_on = not self.music_on
        self.music_btn._off.setVisible(not self.music_on)

    def showEvent(self, e):
        super().showEvent(e)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(250)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)

        group = QParallelAnimationGroup(self)

        def bounce(widget, dur=350, factor=1.1):
            geom = widget.geometry()
            dx, dy = geom.width() * (factor - 1) / 2, geom.height() * (factor - 1) / 2
            bigger = geom.adjusted(-dx, -dy, dx, dy)

            anim = QPropertyAnimation(widget, b"geometry", self)
            anim.setDuration(dur)
            anim.setKeyValueAt(0.0, bigger)
            anim.setKeyValueAt(0.4, geom)
            anim.setKeyValueAt(1.0, geom)
            anim.setEasingCurve(QEasingCurve.OutBack)
            return anim

        group.addAnimation(bounce(self.findChild(QLabel, None)))

        for btn in (self.sound_btn, self.music_btn, self.home_btn):
            group.addAnimation(bounce(btn, dur=1000))

        fade.start()
        group.start()
