from __future__ import annotations

import dataclasses


@dataclasses.dataclass()
class IntelOwlConfig:
    host: str
    port: int
    api_key: str
    http_scheme: str
