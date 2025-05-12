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
from core.board import Board
from core.enums import Bonus
from core.setting_deploy import get_resource_path
from logger import logger


class GameWindow(QMainWindow):
    ROWS = 8
    COLS = 7
    CELL_SIZE = 60
    GRID_ORIGIN = QPoint(40, 300)

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
        self.tile_labels = {}

        self._load_fonts()
        self._init_window()
        self._init_background()
        self._init_title()
        self._init_control_frames()
        self._init_settings_button()
        self._init_board_container()
        self._init_grid()
        self._init_digit_labels()

        self.board = Board()

        self._render_from_board(first=True)

        self.display_number('timer', 789, 'blue')
        self.display_number('score', 123, 'red')

    def _open_settings(self):
        if hasattr(self, "_settings") and self._settings.isVisible():
            return
        self._settings = SettingsWindow(self)
        cx = self.x() + (self.width() - self._settings.width()) // 2
        cy = self.y() + (self.height() - self._settings.height()) // 2
        self._settings.move(cx, cy)
        self._settings.show()

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

    def handle_swap_request(self, a_lbl: TileLabel, b_lbl: TileLabel):
        if abs(a_lbl.row - b_lbl.row) + abs(a_lbl.col - b_lbl.col) != 1:
            return
        self._animate_swap(a_lbl, b_lbl,
                           lambda: self._after_swap_logic(a_lbl, b_lbl))

    def _after_swap_logic(self, a_lbl, b_lbl):
        a = (a_lbl.row, a_lbl.col)
        b = (b_lbl.row, b_lbl.col)

        success, removed, bonuses = self.board.swap(a, b)
        print("removed first wave:", removed)
        if not success:
            self._animate_swap(a_lbl, b_lbl, on_finished=None)
            return

        # --- 1. Анимация удаления первой волны ---
        for r, c in removed:
            lbl = self.tile_labels.pop((r, c), None)
            if not lbl:
                continue

            explosion = ExplosionLabel(self, lbl.element.color.value, lbl.pos(), self.CELL_SIZE, fps=100)

            lbl.deleteLater()

            explosion.raise_()
            explosion.show()

        print(bonuses)
        # --- 2. Появление бонусных плиток ---
        for r, c, bonus in bonuses:
            elem = self.board.cell(r, c)
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)
            x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() + r * self.CELL_SIZE
            lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()
            self.tile_labels[(r, c)] = lbl

        fallen, spawned = self.board.collapse_and_fill()
        print(f"fallen^ {fallen}")
        # 3a: анимируем “старые” плитки
        for elem, new_r, new_c in fallen:
            # ищем метку по объекту element
            for lbl in self.tile_labels.values():
                if lbl.element is elem:
                    lbl.row, lbl.col = new_r, new_c
                    self.tile_labels.pop((elem.y, elem.x), None)  # до смены координат
                    self.tile_labels[(new_r, new_c)] = lbl
                    self._animate_fall(lbl, new_r)
                    break
        self.print_matrix()
        print(f"spawned^ {spawned}")

        for elem in spawned:
            lbl = TileLabel(self, elem)
            pix = self._pix_for_elem(elem)
            lbl.setPixmap(pix)

            x = self.GRID_ORIGIN.x() + elem.y * self.CELL_SIZE
            y = self.GRID_ORIGIN.y() - elem.x * self.CELL_SIZE
            print(f"x {x} y {y}")
            lbl.setGeometry(x, y,
                            self.CELL_SIZE, self.CELL_SIZE)
            lbl.raise_()
            lbl.show()

            self.tile_labels[(elem.x, elem.y)] = lbl
            self._animate_fall(lbl, elem.x)

        self.print_matrix()

    def _animate_swap(self, t1: TileLabel, t2: TileLabel, on_finished=None):
        group = QParallelAnimationGroup(self)
        for tile, end in ((t1, t2.pos()), (t2, t1.pos())):
            anim = QPropertyAnimation(tile, b'pos', self)
            anim.setDuration(150)
            anim.setEndValue(end)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            group.addAnimation(anim)

        def _after_anim():
            self._swap_tiles(t1, t2)
            if on_finished:
                on_finished()

        group.finished.connect(_after_anim)
        group.start()
        self.animations.append(group)
        # чистим уже закончившиеся
        self.animations = [g for g in self.animations if g.state() != QPropertyAnimation.Stopped]

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

    def _pix_for_elem(self, elem):
        if elem is None:
            return None
        root = "assets/elements"
        if elem.bonus == Bonus.NONE:
            img = f"{root}/{elem.color.value}.png"
        elif elem.bonus == Bonus.BOMB:
            img = f"{root}/bomb.png"
        else:
            axis = "h" if elem.bonus == Bonus.ROCKET_H else "v"
            img = f"{root}/rocket_{axis}.png"
        return QPixmap(get_resource_path(img)).scaled(self.CELL_SIZE, self.CELL_SIZE)

    def _render_from_board(self, first=False):
        for lbl in self.tile_labels.values():
            lbl.deleteLater()
        self.tile_labels.clear()

        for r in range(self.ROWS):
            for c in range(self.COLS):
                elem = self.board.cell(r, c)
                pix = self._pix_for_elem(elem)
                lbl = TileLabel(self, elem)
                lbl.setPixmap(pix)
                x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
                y = self.GRID_ORIGIN.y() + (-1 if first else r) * self.CELL_SIZE
                lbl.setGeometry(x, y, self.CELL_SIZE, self.CELL_SIZE)
                lbl.raise_()
                lbl.show()
                self.tile_labels[(r, c)] = lbl
                if first:
                    self._animate_fall(lbl, r)

    def _render_diff(self, old, new):
        removed = []  # какие позиции опустели
        moved = []  # (lbl, new_row)

        # --- проход по старой сетке ------------------------------------------
        pos_of_elem: dict[object, tuple[int, int]] = {}
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if old[r][c]:
                    pos_of_elem[id(old[r][c])] = (r, c)

        for r in range(self.ROWS):
            for c in range(self.COLS):
                o = old[r][c]
                n = new[r][c]

                if o is None:
                    continue

                if n is o:
                    if (r, c) != (n.y, n.x):
                        moved.append((self.tile_labels[(r, c)], n.y))
                        self.tile_labels[(r, c)].row = n.y
                        self.tile_labels[(n.y, n.x)] = self.tile_labels.pop((r, c))
                else:
                    removed.append((r, c))

        # --- взрывы -----------------------------------------------------------
        for r, c in removed:
            lbl = self.tile_labels.pop((r, c), None)
            if lbl:
                ExplosionLabel(self, lbl.element, lbl.pos(),
                               self.CELL_SIZE, fps=120)
                lbl.deleteLater()

        # --- новые элементы ---------------------------------------------------
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if new[r][c] is None:
                    continue
                if (r, c) not in self.tile_labels:
                    # появился новый сверху
                    pix = self._pix_for_elem(new[r][c])
                    lbl = TileLabel(self, new[r][c].color.value, r, c)
                    lbl.setPixmap(pix)
                    x = self.GRID_ORIGIN.x() + c * self.CELL_SIZE
                    lbl.setGeometry(x, self.GRID_ORIGIN.y() - self.CELL_SIZE,
                                    self.CELL_SIZE, self.CELL_SIZE)
                    lbl.raise_()
                    self.tile_labels[(r, c)] = lbl
                    self._animate_fall(lbl, r)

        # --- смещения существующих плиток ------------------------------------
        for lbl, new_row in moved:
            self._animate_fall(lbl, new_row)

    def print_matrix(self):
        for r in range(self.ROWS):
            row_str = ''
            for c in range(self.COLS):
                lbl = self.tile_labels.get((r, c))
                row_str += lbl.element.short() if lbl else '.'
            print(row_str)

    def _swap_tiles(self, tile1: TileLabel, tile2: TileLabel):
        """Поменять местами объекты и их учёт в self.tile_labels."""
        # 1) Забираем старые координаты
        r1, c1 = tile1.row, tile1.col
        r2, c2 = tile2.row, tile2.col

        # 2) Меняем их в самих метках
        tile1.row, tile1.col, tile2.row, tile2.col = r2, c2, r1, c1

        # 3) Меняем ключи в словаре
        # удалим старые записи
        self.tile_labels.pop((r1, c1), None)
        self.tile_labels.pop((r2, c2), None)
        # и запишем по новым
        self.tile_labels[(tile1.row, tile1.col)] = tile1
        self.tile_labels[(tile2.row, tile2.col)] = tile2
