from __future__ import annotations

import asyncio
import typing

import pyintelowl

from analytics.connectors import _common as common

if typing.TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .config import IntelOwlConfig


class IntelOwlQuery:
    connection: pyintelowl.IntelOwl
    job_id: int
    _state: dict[str, typing.Any] | None

    def __init__(
        self,
        connection: pyintelowl.IntelOwl,
        job_id: int,
    ) -> None:
        self.connection = connection
        self.job_id = job_id
        self._state = None

    @property
    def state(self) -> dict[str, typing.Any]:
        """Intermediate results of a pending query.

        Only available after `self.fetch`.
        """
        if self._state is not None:
            return self._state

        errmsg = "need to fetch first"
        raise AttributeError(errmsg, name=__name__)

    async def fetch(self) -> bool:
        """Fetch (possibly incomplete) query results.

        Returns:
            `True` if the query is still pending, `False` otherwise.
        """
        self._state = await asyncio.to_thread(
            self.connection.get_job_by_id, self.job_id
        )
        return not self.done()

    def done(self) -> bool:
        """Check whether all analyzers in `self.state` are finished."""
        return self._state is not None and all(
            report["status"] not in {"RUNNING", "PENDING"}
            for report in self._state["analyzer_reports"]
        )

    async def finish(self, *, sleep: float = 0) -> dict[str, typing.Any]:
        """Wait until all queried analyzers finish and return the results.

        Args:
            sleep: Seconds to sleep after fetching query state.

        Returns:
            Results of the finished query.
        """
        while await self.fetch():  # noqa: ASYNC110
            await asyncio.sleep(sleep)
        return self.state


class IntelOwlConnector:
    connection: pyintelowl.IntelOwl

    def __init__(
        self,
        config: IntelOwlConfig | None = None,
        /,
        **options: typing.Any,
    ) -> None:
        """Create a connection to an IntelOwl server.

        Args:
            config: Connection configuration.
            options: Extra options for `pyintelowl.IntelOwl` (overrides ones
                from `config`).
        """
        if config is not None:
            options.setdefault("token", config.api_key)
            options.setdefault(
                "instance_url",
                f"{config.http_scheme}://{config.host}:{config.port}",
            )
        self.connection = pyintelowl.IntelOwl(**options)

    async def _try_kill_job(self, job_id: int) -> bool:
        try:
            _ = await asyncio.to_thread(
                self.connection.kill_running_job,
                job_id,
            )
        except pyintelowl.IntelOwlClientException as e:
            if e.response is not None and e.response.status_code == 400:  # noqa: PLR2004
                # Job has already finished. We don't mind.
                return False
            raise
        else:
            return True

        # TODO: Maybe also delete the job?

    @common.queryfactory(IntelOwlQuery.finish)
    async def observable_analysis(
        self,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> AsyncIterator[IntelOwlQuery]:
        job: dict[str, typing.Any] = await asyncio.to_thread(
            self.connection.send_observable_analysis_request,
            *args,
            **kwargs,
        )
        job_id = int(job["job_id"])
        try:
            yield IntelOwlQuery(self.connection, job_id)
        finally:
            await self._try_kill_job(job_id)
