from __future__ import annotations

import random
from typing import Callable
from typing import Set, List, Tuple

from GUI.tile_label import TileLabel
from core import protocol as proto
from core.board import Board
from core.element import Element
from core.enums import Color, Bonus


class GameController:
    def __init__(self,
                 mode: str,
                 time: int,
                 nickname: str,
                 is_client: bool = True,
                 on_send: Callable[[bytes], None] | None = None,
                 on_close: Callable[[], None] | None = None):
        self.bonuses = None
        self.removed = None
        self.b_lbl = None
        self.a_lbl = None
        self.spawned = None
        self.fallen = None
        self.exit_nickname = None
        self.mode = mode
        self.time = time
        self.nicknames = None
        self._send = on_send
        self._close_net = on_close
        self.state_ready: Callable[[str], None] | None = None
        self.winner_player = None
        self.step_player = None
        self.my_nickname = nickname
        self.is_client = is_client
        self.value_player = 2
        self.queue = []
        self.board = None
        self.elapsed_seconds = 0
        self.score = 0
        self.is_my_step = False
        self.current = ""

    def _dispatch(self, cmd: str) -> None:
        if self.state_ready:
            self.state_ready(cmd)

    def new_game(self, nicknames):
        self.nicknames = nicknames
        self.current = self.my_nickname
        self.board = Board()

        self.queue = nicknames[:]
        random.shuffle(self.queue)
        self.current = self.queue[0]
        self.is_my_step = self.my_nickname == self.current

        msg = proto.start_game(
            mode=self.mode,
            queue=self.queue,
            nicknames=self.nicknames,
            board=self.board.to_matrix(),
            time_limit=self.time
        )

        if self._send:
            self._send(proto.dumps(msg))

        self._dispatch("start_game")

    def _next_player(self):
        idx = (self.queue.index(self.current) + 1) % len(self.queue)
        return self.queue[idx]

    def completed_swap(self, removed: Set[Tuple[int, int]], bonuses: List[Tuple[int, int, Bonus]]):
        if self._send:
            self._send(proto.dumps(proto.completed_swap(removed=removed, bonuses=bonuses)))

    def swap(self, a_lbl: TileLabel, b_lbl: TileLabel):
        self.current = self._next_player()
        if self._send:
            self._send(proto.dumps(proto.swap(a_lbl=a_lbl.element, b_lbl=b_lbl.element, next_player=self.current)))

    def auto_swap(self, fallen: tuple[list[tuple[Element, int, int]], spawned: list[Element]]):
        self.current = self._next_player()
        if self._send:
            self._send(proto.dumps(proto.auto_swap(fallen=fallen, spawned=spawned,
                                                   board=self.board.to_matrix())))

    def handle_command(self, data):
        if data["command"] == "start_game":
            self.handle_start_game(data)
            return True
        elif data["command"] == "swap":
            self.handle_swap(data)
        elif data["command"] == "completed_swap":
            self.handle_completed_swap(data)
        elif data["command"] == "auto_swap":
            self.handle_auto_swap(data)
        elif data["command"] == "end_game":
            self.end_game(data)

    def handle_start_game(self, data):
        self.queue = data.get("queue_players")
        self.current = data.get("current_player")
        self.is_my_step = self.my_nickname == self.current
        self.board = Board()
        self.time = data.get("time")
        self.board.board_from_matrix(data.get("board"))
        self.nicknames = data.get("nicknames")
        self.mode = data.get("mode")

    def handle_auto_swap(self, data):
        self.fallen = []
        for item in data["fallen"]:
            e = Element(item["x"], item["y"], Color(item["color"]), Bonus[item["bonus"]])
            self.fallen.append((e, item["new_r"], item["new_c"]))
        self.spawned = [
            Element(d["x"], d["y"], Color(d["color"]), Bonus[d["bonus"]])
            for d in data["spawned"]
        ]
        self.current = data.get("next_player")
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True
        self.board.board_from_matrix(data.get("board"))
        self._dispatch("auto_swap")

    def handle_swap(self, data):
        a = data["a_lbl"]
        b = data["b_lbl"]
        self.is_my_step = self.my_nickname == self.current
        if self.mode == "time":
            self.is_my_step = True
        self.a_lbl = Element(a["x"], a["y"], Color(a["color"]), Bonus[a["bonus"]])
        self.b_lbl = Element(b["x"], b["y"], Color(b["color"]), Bonus[b["bonus"]])
        self._dispatch("swap")

    def end_game(self, data):
        self.winner_player = data.get("winner")
        self._dispatch("end_game")

    def win(self):
        if self._send:
            self._send(proto.dumps(proto.end_game(self.my_nickname)))
        self.end_game(proto.end_game(self.my_nickname))

    def close_game(self):
        if self._close_net:
            self._close_net()

    def handle_error(self, nickname: str | None = None):
        self.exit_nickname = nickname
        self._dispatch("error")

    def handle_completed_swap(self, data):
        self.removed = data.get("removed")
        self.bonuses = data.get("bonuses")
        self._dispatch("completed_swap")
