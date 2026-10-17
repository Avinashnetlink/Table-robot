"""Wire format limits shared by the server and its integration tests."""
from __future__ import annotations
import contextvars
import json
SESSION = contextvars.ContextVar("robot_session", default=None)
class SessionGone(ConnectionError):
    pass

def decode_text(raw: str) -> dict:
    if len(raw.encode()) > 16384:
        raise ValueError("text frame too large")
    value = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if not isinstance(value, dict) or not isinstance(value.get("type"), str):
        raise ValueError("expected object with string type")
    return value

def validate_binary(data: bytes) -> tuple[int, bytes]:
    if len(data) < 2:
        raise ValueError("empty binary frame")
    tag, body = data[0], data[1:]
    if tag == ord("A"):
        if len(body) % 2 or len(body) > 1280:
            raise ValueError("invalid PCM frame")
    elif tag == ord("I"):
        if len(body) > 524288 or not (body.startswith(b"\xff\xd8") and body.endswith(b"\xff\xd9")):
            raise ValueError("invalid JPEG envelope")
    else:
        raise ValueError("unknown binary tag")
    return tag, body

def validate_outgoing(msg: dict) -> None:
    kind = msg.get("type")
    if kind == "move":
        direction, duty, ms = msg.get("dir"), msg.get("duty"), msg.get("ms")
        if direction == "stop":
            return
        limit = {"forward": 400, "pivot_left": 250, "pivot_right": 250}.get(direction, 0)
        if type(duty) is not int or type(ms) is not int or not 1 <= duty <= 40 or not 1 <= ms <= limit:
            raise ValueError("move requires forward/pivot, duty 1..40, duration <=400/250 ms")
    if kind == "patrol" and type(msg.get("on")) is not bool:
        raise ValueError("patrol.on must be boolean")
