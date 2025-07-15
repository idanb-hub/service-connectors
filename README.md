# Service connectors

## Connector Design

Each connector is in its own submodule, along with its configuration dataclass.
This dataclass defines options for the connector.
All connectors take an instance of the respective configuration dataclass as
their first, positional-only argument.

Since most connectors wrap third-party API clients, they also take arbitrary
keyword arguments and forward them to their underlying implementation.
These always override options from the configuration dataclass.
If you specify all necessary options this way, you can omit the config
entirely.

Lets use a connector for ordering pizzas as an example.

```py
from analytics.connectors.pizza import PizzaConfig, PizzaConnector

config = PizzaConfig(host="pizzeria.example.com")
pizzeria = PizzaConnector(config, http_timeout=2)
```

Different connectors have different methods that return different results,
but the following principles apply to them all.

### High-level API Access

Most connector methods return awaitable "query" objects.
Awaiting those returns the final query result.

```py
pizza = await pizzeria.order("margherita", size="large")
```

### Low-level API Access

Where the underlying API allows it, the query objects also let you monitor and
control pending queries. This is especially relevant for long-running
queries in interactive applications, where the user might want to cancel a query
that is progressing too slowly.

Besids being awaitable, query objects that support this level of control can
also be used as async context managers. The methods of their managed objects
vary between different query types, but there's always one to fetch the latest
query state and one to check whether that state represents a finished query.

What is important is that upon exiting the context manager, resources associated
with the query are released and the managed query object becomes invalid.
However, the query results still can (and should) be used outside of the context
manager's block.

```py
async with pizzeria.order("margherita") as order:
    while not order.done:
        await order.update()
        print(order.progress)
    pizza = order.result
serve(pizza)
```

Note that without the `print` and `serve` calls, this code would be equivalent
to the previous "[High-level API](#high-level-api-access)" example.

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

## IntelOwl

Requires the `[intelowl]` extra.

### Example

```py
from analytics.connectors.intelowl import IntelOwlConfig, IntelOwlConnector

config = IntelOwlConfig(...)
conn = IntelOwlConnector(config)

# Option 1: Execute a query and wait for its results.
results = await conn.observable_analysis("8.8.8.8", analyzers_requested=[...])

# Option 2: Execute a query and periodically retrieve partial results.
async with conn.observable_analysis("8.8.8.8", analyzers_requested=[...]) as q:
    while await q.poll():
        print(q.job)  # some analyzers might finish sooner than others
    results = q.job
```
