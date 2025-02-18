from __future__ import annotations

import dataclasses


@dataclasses.dataclass()
class TrinoConfig:
    host: str
    port: int
    catalog: str
    schema: str
    http_scheme: str
    auth_username: str
    auth_password: str
