from __future__ import annotations

import datetime
import typing

from . import PluginModel, PluginStatus, PluginType


class TorProject(PluginModel, frozen=True):
    name: typing.Literal["TorProject"]
    process_time: float
    status: PluginStatus
    end_time: datetime.datetime
    parameters: dict[str, typing.Any]
    type: typing.Literal[PluginType.ANALYZER]
    id: int
    report: dict[str, typing.Any]
    errors: list[typing.Any]
    start_time: datetime.datetime
