import json
from typing import Dict, List, Tuple, Any, Set, Union

from core.element import Element
from core.enums import Bonus


def _elem_to_dict(e: Element) -> Dict[str, Any]:
    return {"x": e.x, "y": e.y,
            "color": e.color.value,
            "bonus": e.bonus.name,
            "img": e.img}


def _dict_to_elem(d: Dict[str, Any]) -> Element:
    from core.enums import Color, Bonus
    e = Element(d["x"], d["y"], Color(d["color"]), Bonus[d["bonus"]])
    return e


def dumps(msg: Dict[str, Any]) -> bytes:
    return json.dumps(msg, ensure_ascii=False).encode()


def loads(raw: bytes) -> Dict[str, Any]:
    return json.loads(raw.decode())


def start_game(
        mode: str,
        queue: List[str],
        nicknames: List[str],
        board: List[List[str]],
        time_limit: int
) -> Dict[str, Any]:
    return {
        "command": "start_game",
        "mode": mode,
        "queue_players": queue,
        "current_player": queue[0],
        "nicknames": nicknames,
        "board": board,
        "time_limit": time_limit
    }


def swap(
        a_lbl: Element,
        b_lbl: Element,
        next_player: str,
) -> Dict[str, Any]:
    """
    Одиночный ход (оба режима):
    player    — кто походил,
    a, b      — координаты переставленных плиток,
    score     — текущий счёт у игрока,
    time_left — сколько осталось секунд (в time-mode).
    """
    return {
        "command": "swap",
        "a_lbl": _elem_to_dict(a_lbl),
        "b_lbl": _elem_to_dict(b_lbl),
        "next_player": next_player,
    }


def auto_swap(
        fallen: List[Tuple[Element, int, int]],
        spawned: List[Element],
        board: List[List[str]]
) -> Dict[str, Any]:
    return {
        "command": "auto_swap",
        "fallen": [
            {**_elem_to_dict(e), "new_r": r, "new_c": c}
            for e, r, c in fallen
        ],
        "spawned": [
            _elem_to_dict(e) for e in spawned
        ],
        "board": board,
    }


def update_score(
        score: int
) -> Dict[str, Any]:
    return {
        "command": "score_update",
        "score": score
    }


def time_update(
        time_left: int
) -> Dict[str, Any]:
    return {
        "command": "time_update",
        "time_left": time_left
    }


def completed_swap(
        removed: Set[Tuple[int, int]],
        bonuses: List[Tuple[int, int, Bonus]]
) -> Dict[str, Union[list[list[Any]], list[dict[str, Any]], str]]:
    return {
        "command": "completed_swap",
        "removed": [[r, c] for (r, c) in sorted(removed)],
        "bonuses": [
            {"r": r, "c": c, "bonus": bonus.name}
            for (r, c, bonus) in bonuses
        ]
    }


def end_game(winner: str) -> Dict:
    return {"command": "end_game", "winner": winner}
