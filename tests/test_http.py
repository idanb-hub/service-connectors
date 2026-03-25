from __future__ import annotations

import asyncio
import typing

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from analytics.connectors.http import HTTPConfig, HTTPConnector
from utils.fromenv import fromenv

if typing.TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from yarl import URL


async def test_basic(connector: HTTPConnector[dict[str, str]]):
    data = await connector.get("/test")
    assert data["method"] == "GET"
    assert data["path"] == "/test"
    assert data["body"] == ""


async def test_progress(connector: HTTPConnector[dict[str, str]]):
    content = "XO" * (4096)

    async with connector.post("/test", data=content) as response:
        assert response.content_length is not None

        async for progress, _ in response.receive():
            assert progress <= response.content_length

        data = await response.json()

        assert data["method"] == "POST"
        assert data["path"] == "/test"
        assert data["body"] == content


async def test_read_while_receiving(connector: HTTPConnector[dict[str, str]]):
    async with connector.get("/test") as response:
        async for _ in response.receive():
            with pytest.raises(RuntimeError):
                _ = await response.text()


async def test_concurrency_limit(config: HTTPConfig, server_url: URL):
    connector = HTTPConnector(
        config,
        mode="json",
        base_url=server_url,
        concurrency_limit=1,
    )

    async with connector.get("/test"):
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(1):
                # Blocked by the outer request.
                _ = await connector.get("/test")

    _ = await connector.get("/test")


@pytest.fixture(scope="module")
def config() -> HTTPConfig:
    return fromenv(HTTPConfig, "HTTP_")


@pytest.fixture(scope="module")
async def server_url() -> AsyncIterator[URL]:
    # https://docs.aiohttp.org/en/v3.13.3/testing.html#framework-agnostic-utilities
    app = web.Application()

    async def handler(request: web.Request) -> web.Response:
        data = {
            "method": request.method,
            "path": request.path_qs,
            "body": await request.text(),
        }
        return web.json_response(data)

    _ = app.add_routes([web.route("*", "/{path:.*}", handler)])

    server = TestServer(app)
    await server.start_server()
    yield server.make_url("")
    await server.close()


@pytest.fixture(scope="module")
async def connector(
    config: HTTPConfig,
    server_url: URL,
) -> AsyncIterator[HTTPConnector[dict[str, str]]]:
    connector = HTTPConnector(
        config,
        mode="json",
        base_url=server_url,
    )

    yield typing.cast("HTTPConnector[typing.Any]", connector)
    await connector.close()
