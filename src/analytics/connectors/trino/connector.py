from __future__ import annotations

import asyncio
import contextlib
import itertools
import typing

import trino

from ._monkeypatch import make_execute_non_blocking

if typing.TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from .config import TrinoConfig


# We're going with monkeypatching the trino client for now.
# TODO: Maybe write a proper patch and send a it upstream?
make_execute_non_blocking()


# https://peps.python.org/pep-0249/#threadsafety
_DBAPI_THREADSAFE_CONNECTIONS = 2
if trino.dbapi.threadsafety < _DBAPI_THREADSAFE_CONNECTIONS:
    msg = "trino module does not provide the required level of thread safety"
    raise RuntimeError(msg)


class TrinoConnector:
    connection: trino.dbapi.Connection

    def __init__(self, config: TrinoConfig) -> None:
        self.connection = trino.dbapi.connect(
            host=config.host,
            port=config.port,
            catalog=config.catalog,
            schema=config.schema,
            http_scheme=config.http_scheme,
            auth=trino.auth.BasicAuthentication(
                username=config.auth_username,
                password=config.auth_password,
            ),
        )

    @contextlib.asynccontextmanager
    async def execute(
        self,
        query: str,
        *params: object,
    ) -> AsyncIterator[QueryResults]:
        """Execute a query and prepare to receive its results.

        The returned results are valid only within the context manager's scope.
        When exiting the scope, the query is closed and no more result rows
        can be fetched.
        Similarly, if the query is still being processed by the server,
        it is cancelled.
        """
        cursor = self.connection.cursor()
        try:
            _ = await asyncio.to_thread(cursor.execute, query, params)
            yield QueryResults(cursor)
        finally:
            cursor.close()


class QueryResults:
    """Lazily fetched query results."""

    cursor: trino.dbapi.Cursor
    query: trino.client.TrinoQuery

    def __init__(self, cursor: trino.dbapi.Cursor) -> None:
        query = cursor._query  # noqa: SLF001
        if query is None:
            errmsg = "cursor does not contain a query"
            raise ValueError(errmsg)
        self.query = query
        self.cursor = cursor

    @property
    def schema(self) -> list[trino.dbapi.ColumnDescription]:
        """Schema of the query results.

        Only available once the first row of results has been received.

        Raises:
            AttributeError: The result schema is not yet available.
        """
        # `Cursor.description` blocks if columns are not yet known.
        if self.query._columns is None:  # noqa: SLF001
            errmsg = "result schema is not available yet"
            raise AttributeError(errmsg)
        return self.cursor.description

    @property
    def stats(self) -> dict[object, object]:
        """Information about a pending query, as received from the server."""
        return self.query.stats

    async def pages(self) -> AsyncIterator[list[list[object]]]:
        """Iterate over pages of rows as they are fetched from the server.

        Each iteration fetches and returns one page of rows.
        Empty pages indicate that no results are available yet.
        """
        # The first batch of rows is received in `Cursor.execute`.
        assert self.query.result is not None
        assert self.query.result.rows is not None
        yield self.query.result.rows

        while True:
            page = await asyncio.to_thread(self.query.fetch)
            if self.query.finished:
                break
            yield page

    @typing.overload
    async def collect(self) -> Iterator[list[object]]:
        """Fetch all rows, then return an iterator over them."""

    @typing.overload
    async def collect[Into](
        self,
        factory: Callable[[Iterator[list[object]]], Into],
    ) -> Into:
        """Fetch all rows, then pass them to factory and return the result."""

    async def collect[Into](
        self,
        factory: Callable[[Iterator[list[object]]], Into] | None = None,
    ) -> Into | Iterator[list[object]]:
        rows = itertools.chain.from_iterable(
            [page async for page in self.pages()]
        )
        return rows if factory is None else factory(rows)

    async def __aiter__(self) -> AsyncIterator[list[object]]:
        """Iterate over rows returned by the query (fetched lazily)."""
        async for page in self.pages():
            for row in page:
                yield row
