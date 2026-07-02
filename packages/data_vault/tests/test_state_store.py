import sqlite3

from data_vault import ClosingConnection, connect_state_db


def test_connect_state_db_creates_parent_and_uses_row_factory(tmp_path):
    db_path = tmp_path / "nested" / "state.db"

    with connect_state_db(db_path, ensure_parent=True) as conn:
        assert isinstance(conn, ClosingConnection)
        assert conn.row_factory is sqlite3.Row
        conn.execute("CREATE TABLE sample (id TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO sample (id, value) VALUES ('one', 'stored')")
        row = conn.execute("SELECT * FROM sample WHERE id = 'one'").fetchone()

    assert db_path.exists()
    assert row["value"] == "stored"
