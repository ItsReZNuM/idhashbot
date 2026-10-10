import os
import gc
import sqlite3
import pytest
import database

TEST_DB = "test_users_isolated.db"


@pytest.fixture(autouse=True)
def cleanup():
    gc.collect()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass
    yield
    gc.collect()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass


def test_init_db_and_migration():
    # 1. Create a legacy table without 'language' column
    with sqlite3.connect(TEST_DB) as conn:
        conn.cursor().execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )
        """)
        conn.commit()

    # 2. Call init_db - should automatically detect and add 'language' column
    database.init_db(TEST_DB)

    with sqlite3.connect(TEST_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cursor.fetchall()]
        assert 'language' in cols


def test_add_and_get_user_language():
    database.init_db(TEST_DB)

    # Add user with English language
    database.add_user(1001, "john_doe", "John", language='en', db_name=TEST_DB)
    assert database.get_user_language(1001, db_name=TEST_DB) == 'en'

    # Update language to Russian
    database.set_user_language(1001, 'ru', db_name=TEST_DB)
    assert database.get_user_language(1001, db_name=TEST_DB) == 'ru'

    # Non-existent user
    assert database.get_user_language(9999, db_name=TEST_DB) is None


def test_get_all_user_ids():
    database.init_db(TEST_DB)
    database.add_user(2001, "user1", "U1", language='fa', db_name=TEST_DB)
    database.add_user(2002, "user2", "U2", language='ru', db_name=TEST_DB)

    ids = database.get_all_user_ids(db_name=TEST_DB)
    assert 2001 in ids
    assert 2002 in ids
    assert len(ids) == 2
