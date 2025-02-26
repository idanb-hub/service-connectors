# ruff: noqa: SLF001

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

    def __init__(
        self,
        config: TrinoConfig | None = None,
        /,
        **options: object,
    ) -> None:
        """Create a connection to a trino server.

        Args:
            config: Connection configuration.
            options: Extra options for `trino.dbapi.connect` (overrides ones
                from `config`).
        """
        if config is not None:
            options.setdefault("host", config.host)
            options.setdefault("port", config.port)
            options.setdefault("catalog", config.catalog)
            options.setdefault("schema", config.schema)
            options.setdefault("http_scheme", config.http_scheme)
            options.setdefault(
                "auth",
                trino.auth.BasicAuthentication(
                    username=config.auth_username,
                    password=config.auth_password,
                ),
            )
        self.connection = trino.dbapi.connect(**options)

    @contextlib.asynccontextmanager
    async def execute_lazy(
        self,
        query: str,
        *params: object,
    ) -> AsyncIterator[QueryResults]:
        """Execute a query and prepare to receive its results.

        This context manager sends a query to the server and returns an
        asynchronous iterable though which its results can be fetched.
        Upon exit, the query is closed/cancelled and no more results can be
        fetched.
        """
        cursor = self.connection.cursor()
        try:
            _ = await asyncio.to_thread(cursor.execute, query, params)

            # Do the first fetch right away to fail early when the query is
            # rejected (for example, because of syntax errors).
            assert cursor._query is not None
            rows = await asyncio.to_thread(cursor._query.fetch)

            yield QueryResults(cursor, rows)
        finally:
            cursor.close()

    async def execute(
        self,
        query: str,
        *params: object,
    ) -> Iterator[list[object]]:
        """Execute a query fetch its results.

        Does not return until all results have been fetched.
        Use `execute_lazy` if you need more control.

        Returns:
            Iterator over the fetched rows.
        """
        async with self.execute_lazy(query, *params) as results:
            return await results.collect()


class QueryResults:
    """Lazily fetched query results."""

    cursor: trino.dbapi.Cursor
    query: trino.client.TrinoQuery

    _pages: list[list[list[object]]]

    def __init__(
        self,
        cursor: trino.dbapi.Cursor,
        rows: list[list[object]],
    ) -> None:
        query = cursor._query
        if query is None:
            errmsg = "cursor does not contain a query"
            raise ValueError(errmsg)
        self.query = query
        self.cursor = cursor
        self._pages = [rows]

    async def schema(self) -> list[trino.dbapi.ColumnDescription]:
        """Get the schema of the query results.

        Waits until the first row of results has been received
        (the schema is not available before that).

        Raises:
            ValueError: The query was closed before the schema became available.
        """
        while not (
            self.query._columns is not None
            or self.query.finished
            or self.query.cancelled
        ):
            page = await asyncio.to_thread(self.query.fetch)
            self._pages.append(page)

        description = self.cursor.description
        if description is not None:
            return description

        errmsg = "query was closed before its schema was received"
        raise ValueError(errmsg)

    @property
    def stats(self) -> dict[object, object]:
        """Information about a pending query, as received from the server."""
        return self.query.stats

    async def pages(self) -> AsyncIterator[list[list[object]]]:
        """Iterate over pages of rows as they are fetched from the server.

        Each iteration fetches and returns one page of rows.
        Empty pages indicate that no results are available yet.
        """
        for page in self._pages:
            yield page

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
