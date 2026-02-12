import typing
from collections.abc import AsyncIterator

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from analytics.connectors.http import HTTPConfig, HTTPConnector
from utils.fromenv import fromenv


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


@pytest.fixture(scope="module")
def config() -> HTTPConfig:
    return fromenv(HTTPConfig, "HTTP_")


@pytest.fixture(scope="module")
async def connector(
    config: HTTPConfig,
) -> AsyncIterator[HTTPConnector[dict[str, str]]]:
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

    connector = HTTPConnector(
        config,
        mode="json",
        base_url=server.make_url(""),
    )

    yield typing.cast("HTTPConnector[typing.Any]", connector)

    await connector.close()
    await server.close()
