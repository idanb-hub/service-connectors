from __future__ import annotations

import enum


class JobStatus(enum.StrEnum):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/frontend/src/constants/jobConst.js#L5
    PENDING = "pending"
    RUNNING = "running"
    ANALYZERS_RUNNING = "analyzers_running"
    ANALYZERS_COMPLETED = "analyzers_completed"
    CONNECTORS_RUNNING = "connectors_running"
    CONNECTORS_COMPLETED = "connectors_completed"
    PIVOTS_RUNNING = "pivots_running"
    PIVOTS_COMPLETED = "pivots_completed"
    VISUALIZERS_RUNNING = "visualizers_running"
    VISUALIZERS_COMPLETED = "visualizers_completed"
    REPORTED_WITH_FAILS = "reported_with_fails"
    REPORTED_WITHOUT_FAILS = "reported_without_fails"
    KILLED = "killed"
    FAILED = "failed"

    def isfinal(self) -> bool:
        # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/frontend/src/constants/jobConst.js#L22C1-L27C4
        return self in {
            JobStatus.REPORTED_WITH_FAILS,
            JobStatus.REPORTED_WITHOUT_FAILS,
            JobStatus.KILLED,
            JobStatus.FAILED,
        }


class PluginType(enum.StrEnum):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/frontend/src/constants/pluginConst.js#L9
    ANALYZER = "analyzer"
    CONNECTOR = "connector"
    VISUALIZER = "visualizer"
    INGESTOR = "ingestor"
    PIVOT = "pivot"
    PLAYBOOK = "playbook"


class PluginStatus(enum.StrEnum):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/frontend/src/constants/pluginConst.js#L18
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    KILLED = "KILLED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    def isfinal(self) -> bool:
        # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/frontend/src/constants/pluginConst.js#L26
        return self in {
            PluginStatus.KILLED,
            PluginStatus.SUCCESS,
            PluginStatus.FAILED,
        }
