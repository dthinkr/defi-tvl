import duckdb
import pytest

@pytest.fixture(scope="module")
def db_connection():
    con = duckdb.connect(database=':memory:', read_only=False)
    yield con
    con.close()

def test_upsert_operation(db_connection):
    db_connection.execute("""
    CREATE TABLE test_upsert (
        id INTEGER,
        name VARCHAR,
        value INTEGER,
        PRIMARY KEY (id)
    )
    """)
    db_connection.execute("INSERT INTO test_upsert (id, name, value) VALUES (1, 'A', 10), (2, 'B', 20)")
    db_connection.execute("""
    INSERT INTO test_upsert (id, name, value) VALUES (2, 'B', 25), (3, 'C', 30)
    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, value = EXCLUDED.value
    """)
    result = db_connection.execute("SELECT * FROM test_upsert ORDER BY id").fetchall()
    assert result == [(1, 'A', 10), (2, 'B', 25), (3, 'C', 30)]
    db_connection.execute("DROP TABLE test_upsert")