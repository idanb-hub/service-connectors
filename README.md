# Service connectors

## Trino

Requires the `[trino]` extra.

### Example

```py
from analytics.connectors.trino import TrinoConfig, TrinoConnector

config = TrinoConfig(...)
conn = TrinoConnector(
    config,
    # additional options (extends/overrides config)
    request_timeout=2,
)

# Option 1: Execute a query and wait for its results.
rows = list(await conn.execute("SELECT * FROM table LIMIT ?", 10))

# Option 2: Execute a query and iterate over lazily fetched rows.
async with conn.execute("SELECT * FROM table LIMIT ?", 10) as results:
    async for row in results:
        ...
    # The query is closed/cancelled when exiting the `with` block.
```
