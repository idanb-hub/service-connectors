from __future__ import annotations

import asyncio
import logging
import typing

import certifi
import pyintelowl

from analytics.connectors import _common as common

from .models import Job

if typing.TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .config import IntelOwlConfig


logger = logging.getLogger(__name__)


class IntelOwlQuery:
    connection: pyintelowl.IntelOwl
    job_id: int
    _job: Job | None

    def __init__(
        self,
        connection: pyintelowl.IntelOwl,
        job_id: int,
    ) -> None:
        self.connection = connection
        self.job_id = job_id
        self._job = None

    async def poll(self) -> bool:
        """Fetch (possibly incomplete) query results.

        Returns:
            `True` if the query is still pending, `False` otherwise.
        """
        data = await asyncio.to_thread(
            self.connection.get_job_by_id, self.job_id
        )
        self._job = Job.model_validate(data)
        return not self._job.status.isfinal()

    @property
    def job(self) -> Job:
        assert self._job is not None
        return self._job

    async def finish(self, *, sleep: float = 0) -> Job:
        """Wait until all queried analyzers finish and return the results.

        Args:
            sleep: Seconds to sleep after fetching query state.

        Returns:
            Results of the finished query.
        """
        while await self.poll():  # noqa: ASYNC110
            await asyncio.sleep(sleep)
        return self.job


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
            options.setdefault("certificate", certifi.where())
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
            logger.info("Job killed. ID: %i", job_id)
            return True

        # TODO: Maybe also delete the job?

    @common.queryfactory(IntelOwlQuery.finish)
    @common.copy_argtypes(pyintelowl.IntelOwl.send_observable_analysis_request)
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
            query = IntelOwlQuery(self.connection, job_id)
            # Do the initial poll here so that users don't face errors when
            # they try to access the associated job without polling first.
            await query.poll()
            yield query
        finally:
            await self._try_kill_job(job_id)
