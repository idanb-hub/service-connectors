from __future__ import annotations

import dataclasses


@dataclasses.dataclass()
class HTTPConfig:
    timeout: float = 30.0
