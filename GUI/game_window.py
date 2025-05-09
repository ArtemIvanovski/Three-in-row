import random

from PyQt5.QtCore import QPoint, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QFont
from PyQt5.QtWidgets import (
    QMainWindow, QLabel,
    QFrame, QPushButton
)

from GUI.explosion_label import ExplosionLabel
from GUI.settings_window import SettingsWindow
from GUI.tile_label import TileLabel
from core.setting_deploy import get_resource_path
from logger import logger


class GameWindow(QMainWindow):
    ROWS = 8
    COLS = 7
    CELL_SIZE = 60
    GRID_ORIGIN = QPoint(40, 300)

    # Resources
    ICON_PATH = get_resource_path("assets/icon.png")
    BACKGROUND_PATH = get_resource_path("assets/game_background.png")
    TITLE_PATH = get_resource_path("assets/board.png")
    SETTINGS_ICON = get_resource_path("assets/buttons/settings.png")
    FONT_PATH = get_resource_path("assets/FontFont.otf")

    TILE_IMAGES = {
        name: get_resource_path(f"assets/elements/{name}.png")
        for name in ("orange", "purple", "red", "yellow")
    }
    BLOCK_IMAGES = [
        get_resource_path(f"assets/block{i}.png")
        for i in (1, 2)
    ]

    def __init__(self):
        super().__init__()
        self.animations = []
        self.selected_tile = None
        self._load_fonts()
        self._init_window()
        self._init_background()
        self._init_title()
        self._init_control_frames()
        self._init_settings_button()
        self._init_board_container()
        self._init_grid()
        self._init_digit_labels()
        self._populate_board()

        self.display_number('timer', 789, 'blue')
        self.display_number('score', 123, 'red')

    def _load_fonts(self):
        font_id = QFontDatabase.addApplicationFont(self.FONT_PATH)
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = families[0] if families else self.font().family()

    def _init_window(self):
        self.setWindowTitle("Three in row")
        self.setGeometry(100, 100, 500, 880)
        self.setWindowIcon(QIcon(self.ICON_PATH))
        self.setFixedSize(500, 880)

    def _init_background(self):
        lbl = QLabel(self)
        pix = QPixmap(self.BACKGROUND_PATH).scaled(self.width(), self.height())
        lbl.setPixmap(pix)
        lbl.setGeometry(0, 0, self.width(), self.height())
        lbl.lower()

    def _init_title(self):
        lbl = QLabel(self)
        pix = QPixmap(self.TITLE_PATH).scaled(440, 200)
        lbl.setPixmap(pix)
        lbl.setGeometry(30, 0, 440, 200)
        lbl.raise_()

    def _init_control_frames(self):
        coords = {'timer': (100, 70), 'score': (280, 70)}
        self.control_frames = {}
        for key, (x, y) in coords.items():
            frame = QFrame(self)
            frame.setGeometry(x, y, 120, 85)
            frame.setStyleSheet(
                "QFrame { background-color: rgb(254,243,219); "
                "border:1px solid #000; border-radius:6px;}"
            )
            self.control_frames[key] = frame
            lbl = QLabel('Время' if key == 'timer' else 'Счёт', self)
            lbl.setFont(QFont(self.font_family, 18))
            lbl.setStyleSheet("color: #000;")
            lbl.setGeometry(x + 20, 20, 200, 50)
            lbl.raise_()

    def _init_settings_button(self):
        btn = QPushButton(self)
        btn.setIcon(QIcon(self.SETTINGS_ICON))
        btn.setIconSize(QSize(40, 40))
        btn.setGeometry(420, 140, 40, 40)
        btn.setFlat(True)
        btn.clicked.connect(self._open_settings)

    def _init_board_container(self):
        x, y = self.GRID_ORIGIN.x() - 10, self.GRID_ORIGIN.y() - 10
        w, h = self.COLS * self.CELL_SIZE + 20, self.ROWS * self.CELL_SIZE + 20
        frame = QFrame(self)
        frame.setGeometry(x, y, w, h)
        frame.setStyleSheet(
            "QFrame { background-color: rgba(14,99,167,200); "
            "border:3px solid #000; border-radius:6px;}"
        )
        frame.lower()
        self.board_container = frame

    def _init_grid(self):
        self.background_labels = []
        for r in range(self.ROWS):
            row_labels = []
            for c in range(self.COLS):
                lbl = QLabel(self)
                lbl.setPixmap(
                    QPixmap(self.BLOCK_IMAGES[(r + c) % 2])
                    .scaled(self.CELL_SIZE, self.CELL_SIZE)
                )
                lbl.setGeometry(
                    self.GRID_ORIGIN.x() + c * self.CELL_SIZE,
                    self.GRID_ORIGIN.y() + r * self.CELL_SIZE,
                    self.CELL_SIZE, self.CELL_SIZE
                )
                lbl.raise_()
                row_labels.append(lbl)
            self.background_labels.append(row_labels)

    def _init_digit_labels(self):
        self.digit_labels = {'timer': [], 'score': []}

    def _animate_fall(self, tile: TileLabel, target_row: int, finished=None):
        start = tile.pos()
        end = QPoint(start.x(),
                     self.GRID_ORIGIN.y() + target_row * self.CELL_SIZE)

        dist = end.y() - start.y()
        dur = 100 + dist * 2
        anim = QPropertyAnimation(tile, b'pos', self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(dur)
        anim.setEasingCurve(QEasingCurve.OutBounce)

        if finished:
            anim.finished.connect(finished)
        anim.start()
        self.animations.append(anim)

    def _populate_board(self):
        self.grid = [[None] * self.COLS for _ in range(self.ROWS)]
        for r in range(self.ROWS):
            for c in range(self.COLS):
                self._spawn_tile(r, c, random.choice(list(self.TILE_IMAGES)), True)

    def _spawn_tile(self, r, c, elem, from_top=False):
        pix = QPixmap(self.TILE_IMAGES[elem]).scaled(self.CELL_SIZE, self.CELL_SIZE)
        t = TileLabel(self, elem, r, c)
        t.setPixmap(pix)

        x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
        y_final = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
        if from_top:
            y_start = self.GRID_ORIGIN.y() - self.CELL_SIZE
            t.setGeometry(x, y_start, self.CELL_SIZE, self.CELL_SIZE)
            t.raise_()
            self._animate_fall(t, r)
        else:
            t.setGeometry(x, y_final, self.CELL_SIZE, self.CELL_SIZE)
            t.raise_()

        self.grid[r][c] = t

    def _apply_gravity(self):
        for col in range(self.COLS):
            write_row = self.ROWS - 1
            for read_row in range(self.ROWS - 1, -1, -1):
                tile = self.grid[read_row][col]
                if tile:
                    if read_row != write_row:
                        self.grid[write_row][col] = tile
                        self.grid[read_row][col] = None
                        tile.row = write_row
                        self._animate_fall(tile, write_row)
                    write_row -= 1

            for row in range(write_row, -1, -1):
                elem = random.choice(list(self.TILE_IMAGES))
                self._spawn_tile(row, col, elem, from_top=True)

    def handle_swap_request(self, a: TileLabel, b: TileLabel):
        if abs(a.row - b.row) + abs(a.col - b.col) != 1:
            return
        self._animate_swap(a, b, lambda: self._after_first_swap(a, b))

    def _after_first_swap(self, a: TileLabel, b: TileLabel):
        if self._forms_match_after_swap(a, b):
            self._commit_swap(a, b)
            self._destroy_matches()
        else:
            self._animate_swap(a, b)

    def _destroy_matches(self):
        matched = self._collect_matches()
        if not matched:
            return

        last_boom = None
        for r, c in matched:
            tile = self.grid[r][c]
            if not tile:
                continue
            last_boom = ExplosionLabel(self, tile.element, tile.pos(), self.CELL_SIZE, fps=200)
            tile.deleteLater()
            self.grid[r][c] = None
            last_boom.destroyed.connect(self._apply_gravity)

    def _collect_matches(self):
        matches = set()
        for r in range(self.ROWS):
            run = [(r, 0)]
            for c in range(1, self.COLS):
                if self.grid[r][c] and self.grid[r][c - 1] and self.grid[r][c].element == self.grid[r][c - 1].element:
                    run.append((r, c))
                else:
                    if len(run) >= 3:
                        matches.update(run)
                    run = [(r, c)]
            if len(run) >= 3:
                matches.update(run)
        for c in range(self.COLS):
            run = [(0, c)]
            for r in range(1, self.ROWS):
                if self.grid[r][c] and self.grid[r - 1][c] and self.grid[r][c].element == self.grid[r - 1][c].element:
                    run.append((r, c))
                else:
                    if len(run) >= 3:
                        matches.update(run)
                    run = [(r, c)]
            if len(run) >= 3:
                matches.update(run)
        return matches

    def _commit_swap(self, a: TileLabel, b: TileLabel):
        self.grid[a.row][a.col], self.grid[b.row][b.col] = b, a
        a.row, b.row = b.row, a.row
        a.col, b.col = b.col, a.col
        logger.info('Swap committed')

    def _animate_swap(self, t1: TileLabel, t2: TileLabel, on_finished=None):
        group = QParallelAnimationGroup(self)
        for tile, end in ((t1, t2.pos()), (t2, t1.pos())):
            anim = QPropertyAnimation(tile, b'pos', self)
            anim.setDuration(150)
            anim.setEndValue(end)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            group.addAnimation(anim)
        if on_finished:
            group.finished.connect(on_finished)
        group.start()
        self.animations.append(group)
        self.animations = [g for g in self.animations if g.state() != QPropertyAnimation.Stopped]

    def _forms_match_after_swap(self, a: TileLabel, b: TileLabel) -> bool:
        def elem_at(r, c):
            if (r, c) == (a.row, a.col):
                return b.element
            if (r, c) == (b.row, b.col):
                return a.element
            return self.grid[r][c].element

        return any(self._has_line(r, c, elem_at) for r, c in {(a.row, a.col), (b.row, b.col)})

    def _has_line(self, r, c, elem_at):
        target = elem_at(r, c)

        def count(dir_r, dir_c):
            i, j = r + dir_r, c + dir_c
            cnt = 0
            while 0 <= i < self.ROWS and 0 <= j < self.COLS and elem_at(i, j) == target:
                cnt += 1
                i += dir_r
                j += dir_c
            return cnt

        horiz = count(0, -1) + 1 + count(0, 1)
        vert = count(-1, 0) + 1 + count(1, 0)
        return horiz >= 3 or vert >= 3

    def display_number(self, kind, value, color, x=None, y=None):
        if x is None or y is None:
            coords = {'timer': (125, 95), 'score': (305, 95)}
            x, y = coords[kind]
        for lbl in self.digit_labels[kind]:
            lbl.deleteLater()
        self.digit_labels[kind].clear()
        for i, ch in enumerate(str(value)):
            path = get_resource_path(f"assets/score/{color}/{ch}.png")
            pix = QPixmap(path)
            lbl = QLabel(self)
            lbl.setPixmap(pix)
            w, h = pix.width(), pix.height()
            lbl.setGeometry(x + i * w, y, w, h)
            lbl.raise_()
            self.digit_labels[kind].append(lbl)

    def _open_settings(self):
        if hasattr(self, "_settings") and self._settings.isVisible():
            return
        self._settings = SettingsWindow(self)
        cx = self.x() + (self.width() - self._settings.width()) // 2
        cy = self.y() + (self.height() - self._settings.height()) // 2
        self._settings.move(cx, cy)
        self._settings.show()
