# core/board.py
from __future__ import annotations
import random
from typing import List, Tuple, Dict, Iterable

from core.enums import Color, Bonus
from core.element import Element


class Board:
    """Логика игрового поля “3-в-ряд” без графики и сети."""
    ROWS, COLS = 8, 7
    COLORS = list(Color)

    # ------------------------------------------------------------------ ctor
    def __init__(self):
        self.grid: List[List[Element | None]] = [
            [None] * self.COLS for _ in range(self.ROWS)
        ]
        self._fill_start_board()

    # ---------------------------------------------------------------- public
    def cell(self, r: int, c: int) -> Element | None:
        return self.grid[r][c]

    def swap(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        """Пробует поменять местами; если после этого нет линий – откат."""
        (r1, c1), (r2, c2) = a, b
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        if self._any_matches_after({a, b}):
            self._resolve_all()  # взрываем, падаем, дополняем
            return True
        # откат
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        return False

    def has_move(self) -> bool:
        """Есть ли хоть один допустимый обмен, дающий линию."""
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if c + 1 < self.COLS and self._will_match((r, c), (r, c + 1)):
                    return True
                if r + 1 < self.ROWS and self._will_match((r, c), (r + 1, c)):
                    return True
        return False

    # --------------------------------------------------------- инициализация
    def _fill_start_board(self):
        """Генерируем поле без линий, но чтобы ход точно существовал."""
        while True:
            for r in range(self.ROWS):
                for c in range(self.COLS):
                    self.grid[r][c] = Element(r, c, random.choice(self.COLORS))
            if not self._collect_matches() and self.has_move():
                break

    # ----------------------------------------------------------- матч-логика
    def _any_matches_after(self, cells: Iterable[Tuple[int, int]]) -> bool:
        """Проверяем линии только вокруг изменённых ячеек."""
        for r, c in cells:
            if self._line_length(r, c, 0, 1) >= 3 or self._line_length(r, c, 1, 0) >= 3:
                return True
        return False

    def _line_length(self, r: int, c: int, dr: int, dc: int) -> int:
        color = self.grid[r][c].color
        cnt = 1
        i, j = r + dr, c + dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j].color == color:
            cnt += 1;
            i += dr;
            j += dc
        i, j = r - dr, c - dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j].color == color:
            cnt += 1;
            i -= dr;
            j -= dc
        return cnt

    def _collect_matches(self) -> set[Tuple[int, int]]:
        matches = set()
        # горизонтали
        for r in range(self.ROWS):
            run = [(r, 0)]
            for c in range(1, self.COLS):
                cur, prev = self.grid[r][c], self.grid[r][c - 1]
                if cur.color == prev.color:
                    run.append((r, c))
                else:
                    if len(run) >= 3: matches.update(run)
                    run = [(r, c)]
            if len(run) >= 3: matches.update(run)
        # вертикали
        for c in range(self.COLS):
            run = [(0, c)]
            for r in range(1, self.ROWS):
                cur, prev = self.grid[r][c], self.grid[r - 1][c]
                if cur.color == prev.color:
                    run.append((r, c))
                else:
                    if len(run) >= 3: matches.update(run)
                    run = [(r, c)]
            if len(run) >= 3: matches.update(run)
        return matches

    def _resolve_all(self):
        """Полный цикл: уничтожить линии → бонусы → гравитация → дополнить."""
        while True:
            matched = self._collect_matches()
            if not matched:
                break
            self._create_bonuses(matched)
            for r, c in matched:
                self.grid[r][c] = None
            self._gravity()
            self._fill_columns()

    # --------------------------------------------------------------- бонусы
    def _create_bonuses(self, matched: set[Tuple[int, int]]):
        """Создаём ракеты/бомбы на месте одного из элементов линии."""
        by_color: Dict[Tuple[int, int, Color], List[Tuple[int, int]]] = {}
        for r, c in matched:
            color = self.grid[r][c].color
            key = (r, c, color)
            by_color.setdefault(key, []).append((r, c))

        for key, cells in by_color.items():
            if len(cells) == 4:
                r, c = random.choice(cells)
                bonus = Bonus.ROCKET_H if random.choice([0, 1]) else Bonus.ROCKET_V
                self.grid[r][c] = Element(r, c, self.grid[r][c].color, bonus)
            elif len(cells) >= 5:
                r, c = random.choice(cells)
                self.grid[r][c] = Element(r, c, self.grid[r][c].color, Bonus.BOMB)

    # ---------------------------------------------------------- падение/долив
    def _gravity(self):
        for col in range(self.COLS):
            write = self.ROWS - 1
            for read in range(self.ROWS - 1, -1, -1):
                if self.grid[read][col] is not None:
                    if read != write:
                        elem = self.grid[read][col]
                        self.grid[write][col] = elem;
                        self.grid[read][col] = None
                        elem.y = write
                    write -= 1

    def _fill_columns(self):
        for col in range(self.COLS):
            for row in range(self.ROWS):
                if self.grid[row][col] is None:
                    new = Element(row, col, random.choice(self.COLORS))
                    self.grid[row][col] = new

    # ---------------------------------------------------------- вспомогательное
    def _will_match(self, a, b) -> bool:
        (r1, c1), (r2, c2) = a, b
        g = self.grid
        g[r1][c1], g[r2][c2] = g[r2][c2], g[r1][c1]
        ok = self._any_matches_after({a, b})
        g[r1][c1], g[r2][c2] = g[r2][c2], g[r1][c1]
        return ok
