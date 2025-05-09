import json
from typing import Dict, List


def start_game(top: Card,
               queue: List[str],
               hands: Dict[str, List[Card]],
               deck: List[Card],
               nicknames: List[str]) -> Dict:
    return {
        "command": "start_game",
        "value_numbers": len(queue),
        "queue_players": queue,
        "current_player": queue[0],
        "top_card": _card_dict(top),
        "deck": [_card_dict(c) for c in deck],
        "players": {n: [_card_dict(c)
                        for c in hand]
                    for n, hand in hands.items()},
        "nicknames": nicknames
    }


def step(player: str, card: Card, next_player: str) -> Dict:
    return {
        "command": "step",
        "player": player,
        "top_card": _card_dict(card),
        "next_player": next_player,
    }


def end_game(winner: str, score: int) -> Dict:
    return {"command": "end_game", "winner": winner, "score": score}


def dumps(msg: Dict) -> bytes:
    return json.dumps(msg, ensure_ascii=False).encode()


def loads(raw: bytes) -> Dict:
    return json.loads(raw.decode())
