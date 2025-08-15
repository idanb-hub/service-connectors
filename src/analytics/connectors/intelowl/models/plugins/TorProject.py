from __future__ import annotations

import typing

from ..base import PluginModel, PluginType


class TorProject(PluginModel, frozen=True):
    name: typing.Literal["TorProject"]
    type: typing.Literal[PluginType.ANALYZER]
    report: Report


class Report(typing.TypedDict):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/tor.py#L25
    found: bool
