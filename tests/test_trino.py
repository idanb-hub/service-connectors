import asyncio
import os

import pytest
import trino

from analytics.connectors.trino import TrinoConfig, TrinoConnector
from utils.fromenv import fromenv


async def test_basic(connector: TrinoConnector):
    rows = await connector.execute("SELECT ?", 42)
    assert next(rows) == [42]
    with pytest.raises(StopIteration):
        next(rows)


async def test_collect(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute_lazy(query, limit) as results:
        rows = await results.collect(list)

    assert len(rows) == limit


async def test_iter(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute_lazy(query, limit) as results:
        rows = [row async for row in results]

    assert len(rows) == limit


async def test_pages(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute_lazy(query, limit) as results:
        rowcount = 0
        async for page in results.pages():
            rowcount += len(page)

    assert rowcount == limit


async def test_syntax_error(connector: TrinoConnector):
    with pytest.raises(trino.exceptions.TrinoUserError) as exc_info:
        async with connector.execute_lazy("INVALID SYNTAX TEST"):
            pass

    assert exc_info.value.error_name == "SYNTAX_ERROR"


async def test_cancel(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table}"

    async with connector.execute_lazy(query) as results:
        await asyncio.sleep(1)

    assert results.query.cancelled


async def test_schema(connector: TrinoConnector):
    async with connector.execute_lazy("SELECT 1, 2, 3") as results:
        await results.collect(list)

    schema = await results.schema()
    assert len(schema) == 3


async def test_schema_raises(connector: TrinoConnector):
    async with connector.execute_lazy("SELECT 1, 2, 3") as results:
        pass

    with pytest.raises(ValueError, match="query was closed"):
        await results.schema()


async def test_schema_waits(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute_lazy(query, limit) as results:
        schema = await results.schema()
        rows = await results.collect(list)

    assert len(rows) == limit
    assert len(schema) == len(rows[0])


@pytest.fixture(scope="module")
def config() -> TrinoConfig:
    return fromenv(TrinoConfig, "TRINO_")


@pytest.fixture(scope="module")
def connector(config: TrinoConfig) -> TrinoConnector:
    return TrinoConnector(
        config,
        request_timeout=2,
        max_attempts=1,
    )


@pytest.fixture(scope="module")
def table() -> str:
    return os.environ["TRINO_TABLE"]


@pytest.fixture(scope="module", autouse=True)
def ensure_connection(connector: TrinoConnector):
    try:
        connector.connection.cursor().execute("SELECT 1").fetchall()
    except trino.exceptions.Error:
        pytest.fail("could not connect to trino server", pytrace=False)
