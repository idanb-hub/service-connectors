import asyncio
import os

import pytest

from analytics.connectors.trino import TrinoConfig, TrinoConnector
from utils.fromenv import fromenv


async def test_collect(connector: TrinoConnector):
    async with connector.execute("SELECT ?", 42) as results:
        rows = await results.collect(list)

    assert len(rows) == 1
    assert rows[0] == [42]


async def test_iter(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute(query, limit) as results:
        rows = [row async for row in results]

    assert len(rows) == limit


async def test_pages(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute(query, limit) as results:
        rowcount = 0
        async for page in results.pages():
            rowcount += len(page)

    assert rowcount == limit


async def test_cancel(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table}"

    async with connector.execute(query) as results:
        await asyncio.sleep(1)

    assert results.query.cancelled


async def test_schema(connector: TrinoConnector):
    async with connector.execute("SELECT 1, 2, 3") as results:
        await results.collect(list)

    schema = await results.schema()
    assert len(schema) == 3


async def test_schema_raises(connector: TrinoConnector):
    async with connector.execute("SELECT 1, 2, 3") as results:
        pass

    with pytest.raises(ValueError, match="query was closed"):
        await results.schema()


async def test_schema_waits(connector: TrinoConnector, table: str):
    query = f"SELECT * FROM {table} LIMIT ?"
    limit = 100

    async with connector.execute(query, limit) as results:
        schema = await results.schema()
        rows = await results.collect(list)

    assert len(rows) == limit
    assert len(schema) == len(rows[0])


@pytest.fixture
def config() -> TrinoConfig:
    return fromenv(TrinoConfig, "TRINO_")


@pytest.fixture
def connector(config: TrinoConfig) -> TrinoConnector:
    return TrinoConnector(config)


@pytest.fixture
def table() -> str:
    return os.environ["TRINO_TABLE"]
