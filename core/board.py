# core/board.py
from __future__ import annotations
import random
from typing import List, Tuple, Dict, Iterable, Set

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

    def swap(self,
             a: Tuple[int, int],
             b: Tuple[int, int]
             ) -> Tuple[bool, Set[Tuple[int, int]], List[Tuple[int, int, Bonus]]]:
        """
        Делает обмен a<->b, возвращает:
          - success: bool
          - removed: set[(r,c)] — без бонусных клеток
          - bonuses: list[(r,c, bonus_type)]
        """
        r1, c1 = a;
        r2, c2 = b
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        if not self._any_matches_after({a, b}):
            # откат
            self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
            return False, set(), []

        # первая волна
        matched = self._collect_matches()
        # создаём все бонусы и получаем список клеток, где они появились
        bonus_cells = self._create_bonuses(matched, a, b)
        # удаляем всё, кроме бонусов
        to_remove = matched - set((r, c) for r, c, _ in bonus_cells)
        for r, c in to_remove:
            self.grid[r][c] = None
        print(self)
        return True, matched, bonus_cells

    def _create_bonuses(self,
                        matched: Set[Tuple[int, int]],
                        a: Tuple[int, int],
                        b: Tuple[int, int]
                        ) -> List[Tuple[int, int, Bonus]]:
        """
        matched — полный сет координат первой волны,
        a, b — только что переставленные плитки.
        Возвращает список (r,c,bonus), не изменяя matched.
        """
        bonuses = []
        used = set()

        # вспомог: обработать один run (список координат одного ряда/столбца)
        def make_bonus(run: List[Tuple[int, int]]):
            size = len(run)
            if size < 4:
                return
            # выбираем target
            target = next((cell for cell in (a, b) if cell in run), None)
            if target is None:
                # центр руна
                target = run[size // 2]
            r, c = target
            base = self.grid[r][c]
            col = base.color
            if size == 4:
                bonus = random.choice([Bonus.ROCKET_H, Bonus.ROCKET_V])
            else:
                bonus = Bonus.BOMB
            # ставим
            self.grid[r][c] = Element(r, c, col, bonus)
            bonuses.append((r, c, bonus))
            used.update(run)

        # 1) горизонтальные руны
        for r in range(self.ROWS):
            run: List[Tuple[int, int]] = []
            prev_color = None
            for c in range(self.COLS):
                cell = (r, c)
                elem = self.grid[r][c]
                if elem and (prev_color is None or elem.color == prev_color):
                    run.append(cell)
                else:
                    make_bonus(run)
                    run = [cell]
                prev_color = elem.color if elem else None
            make_bonus(run)

        # 2) вертикальные руны
        for c in range(self.COLS):
            run = []
            prev_color = None
            for r in range(self.ROWS):
                cell = (r, c)
                elem = self.grid[r][c]
                if elem and (prev_color is None or elem.color == prev_color):
                    run.append(cell)
                else:
                    make_bonus(run)
                    run = [cell]
                prev_color = elem.color if elem else None
            make_bonus(run)

        return bonuses

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

    def _line_length(self, r, c, dr, dc) -> int:
        start = self.grid[r][c]
        if start is None:  # <<<
            return 0
        color = start.color
        cnt = 1
        i, j = r + dr, c + dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j] and self.grid[i][j].color == color:
            cnt += 1
            i += dr
            j += dc
        i, j = r - dr, c - dc
        while 0 <= i < self.ROWS and 0 <= j < self.COLS and self.grid[i][j] and self.grid[i][j].color == color:
            cnt += 1
            i -= dr
            j -= dc
        return cnt

    def _collect_matches(self) -> set[tuple[int, int]]:
        matches = set()
        # горизонтали
        for r in range(self.ROWS):
            run = []
            for c in range(self.COLS):
                cur = self.grid[r][c]
                if not run or (cur and run[-1] and cur.color == run[-1].color):
                    run.append(cur)
                else:
                    if len(run) >= 3:
                        matches.update({(r, x) for x in range(c - len(run), c)})
                    run = [cur]
            if len(run) >= 3:
                matches.update({(r, x) for x in range(self.COLS - len(run), self.COLS)})

        # вертикали
        for c in range(self.COLS):
            run = []
            for r in range(self.ROWS):
                cur = self.grid[r][c]
                if not run or (cur and run[-1] and cur.color == run[-1].color):
                    run.append(cur)
                else:
                    if len(run) >= 3:
                        matches.update({(y, c) for y in range(r - len(run), r)})
                    run = [cur]
            if len(run) >= 3:
                matches.update({(y, c) for y in range(self.ROWS - len(run), self.ROWS)})

        return matches

    def _activate_bonus(self, pos: tuple[int, int], bonus: Bonus) -> tuple[bool, Set[tuple[int, int]]]:
        """Сработал бонус в pos: сразу убираем нужные клетки."""
        r0, c0 = pos
        removed: Set[tuple[int, int]] = set()

        if bonus == Bonus.BOMB:
            # 3×3 вокруг
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r, c = r0 + dr, c0 + dc
                    if 0 <= r < self.ROWS and 0 <= c < self.COLS:
                        removed.add((r, c))

        elif bonus == Bonus.ROCKET_H:
            # весь ряд r0
            for c in range(self.COLS):
                removed.add((r0, c))

        elif bonus == Bonus.ROCKET_V:
            # весь столбец c0
            for r in range(self.ROWS):
                removed.add((r, c0))

        # удаляем бонусную ячейку и всё вокруг
        for r, c in removed:
            self.grid[r][c] = None

        return True, removed

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

    def __str__(self):
        rows = []
        for row in self.grid:
            row_str = ' '
            for elem in row:
                if elem is None:
                    row_str += '.'
                else:
                    symbol = elem.color.value[0]
                    if elem.bonus:
                        if elem.bonus == Bonus.ROCKET_H:
                            symbol = 'h'
                        elif elem.bonus == Bonus.ROCKET_V:
                            symbol = 'v'
                        elif elem.bonus == Bonus.BOMB:
                            symbol = 'B'
                    row_str += symbol
            rows.append(row_str)
        return '\n'.join(rows)
