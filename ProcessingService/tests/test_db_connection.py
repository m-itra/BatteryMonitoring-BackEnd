from unittest.mock import patch

from app.db import connection


def test_get_sessionmaker_reuses_same_loop_and_separates_different_loops():
    connection._sessionmakers.clear()
    loop_a = object()
    loop_b = object()
    engine_a = object()
    engine_b = object()
    sessionmaker_a = object()
    sessionmaker_b = object()

    with (
        patch("app.db.connection.create_async_engine", side_effect=[engine_a, engine_b]) as create_engine_mock,
        patch("app.db.connection.async_sessionmaker", side_effect=[sessionmaker_a, sessionmaker_b]) as sessionmaker_mock,
        patch("app.db.connection.asyncio.get_running_loop", side_effect=[loop_a, loop_a, loop_b]),
    ):
        first = connection.get_sessionmaker()
        second = connection.get_sessionmaker()
        third = connection.get_sessionmaker()

    assert first is sessionmaker_a
    assert second is sessionmaker_a
    assert third is sessionmaker_b
    assert create_engine_mock.call_count == 2
    assert sessionmaker_mock.call_count == 2
