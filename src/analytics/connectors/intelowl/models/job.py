from __future__ import annotations

# Pydantic fails to generate schema when this is not here. Don't know why.
import typing  # noqa: F401

# Not in a type-checking block because Pydantic needs field types at runtime.
from .base import DictModel, PluginList
from .constants import JobStatus


class Job(DictModel, frozen=True):
    status: JobStatus
    analyzer_reports: PluginList = PluginList()
