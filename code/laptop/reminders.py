"""Local reminder storage and time parsing, independent of networking."""
from __future__ import annotations
import datetime as dt
import pathlib
import re
import sqlite3

class Reminders:
    def __init__(self, path: pathlib.Path) -> None:
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS reminders ("
            " id INTEGER PRIMARY KEY, due TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'task',"
            " title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
        )
        self.db.commit()

    def add(self, due: dt.datetime, title: str, kind: str = "task") -> int:
        cur = self.db.execute(
            "INSERT INTO reminders (due, kind, title) VALUES (?, ?, ?)", (due.isoformat(timespec="minutes"), kind, title)
        )
        self.db.commit()
        return cur.lastrowid

    def due(self) -> list[tuple[int, str, str]]:
        now = dt.datetime.now().isoformat(timespec="minutes")
        return self.db.execute(
            "SELECT id, kind, title FROM reminders WHERE done = 0 AND due <= ? ORDER BY due", (now,)
        ).fetchall()

    def pending(self) -> list[tuple[int, str, str, str]]:
        return self.db.execute("SELECT id, due, kind, title FROM reminders WHERE done = 0 ORDER BY due").fetchall()

    def done(self, rid: int) -> None:
        self.db.execute("UPDATE reminders SET done = 1 WHERE id = ?", (rid,))
        self.db.commit()


def parse_when(words: list[str]) -> tuple[dt.datetime, list[str]] | None:
    """'18:30 ...' (today or tomorrow) or '2026-10-14 18:30 ...'."""
    now = dt.datetime.now()
    try:
        if len(words) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", words[0]):
            when = dt.datetime.fromisoformat(f"{words[0]} {words[1]}")
            return when, words[2:]
        if words and re.fullmatch(r"\d{1,2}:\d{2}", words[0]):
            h, m = map(int, words[0].split(":"))
            when = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if when <= now:
                when += dt.timedelta(days=1)
            return when, words[1:]
    except ValueError:
        return None
    return None


