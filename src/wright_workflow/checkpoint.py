"""A single local owner and transactional checkpoint for each standalone run."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .contracts import canonical_json
from .paths import ConfinedDirectory


@contextmanager
def own_run(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    ConfinedDirectory._reject_existing_links(directory.absolute())
    confined = ConfinedDirectory(directory)
    lock = confined.resolve("wright-owner.lock")
    with lock.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError("This run already has an active owner.") from error
        db = sqlite3.connect(confined.resolve("wright-run.sqlite3"))
        try:
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)"
            )
            db.commit()
            yield RunStore(db, confined.resolve("files"))
        finally:
            db.close()


class RunStore:
    def __init__(self, db, files):
        self.db = db
        self.files = files

    def read(self):
        row = self.db.execute("SELECT body FROM checkpoint WHERE id=1").fetchone()
        if not row:
            return None
        state = json.loads(row[0])
        if state["status"] == "in_flight":
            state["status"] = "outcome_unknown"
            state["attempts"][-1]["outcome"] = "outcome_unknown"
            self.save(state)
        return state

    def save(self, state):
        with self.db:
            self.db.execute(
                "INSERT INTO checkpoint(id,body) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                (canonical_json(state),),
            )
