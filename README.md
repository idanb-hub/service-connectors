# Service connectors

## Trino

Requires the `[trino]` extra.

### Example

```py
from analytics.connectors.trino import TrinoConfig, TrinoConnector

conf = TrinoConfig(...)
conn = TrinoConnector(conf)

async with conn.execute("SELECT * FROM table LIMIT ?", 10) as results:
    # Option 1: Iterate over (lazily fetched) rows.
    async for row in results: ...

    # Option 2: Fetch and return all rows at once.
    rows = await results.collect(list)

    # The query is closed/cancelled when exiting the `with` block.
```
