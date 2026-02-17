# BridgeBase Python SDK

**BridgeBase** is a Python SDK for connecting to databases through a secure gateway using JWT authentication. The SDK handles all the infrastructure (gateway resolution, socket connection, local proxy) and returns native library clients directly — no wrappers, full access to every feature.

## Supported Databases

- **TigerBeetle** — via `tigerbeetle()` → returns `tigerbeetle.ClientSync`
- **Redis / Valkey** — via `redis()` → returns `redis.Redis`

## Features

- 🔐 **JWT Authentication** — Secure gateway authentication with JWT tokens
- 🌐 **Auto Gateway Resolution** — No region required; resolved automatically from JWT
- 🔄 **Local Proxy** — Transparent TCP proxy forwarding traffic through the gateway
- 🚀 **Native Clients** — Returns `tigerbeetle.ClientSync`, `redis.Redis`, etc. directly
- ⚡ **Lazy Initialization** — No network calls until you call `connect()` or use context manager
- 🎯 **Unified API** — Access all TigerBeetle types through a single import

## Installation

```bash
pip install bridgebase[all]           # Everything
```

Install with optional database drivers:

```bash
pip install bridgebase[tigerbeetle]   # TigerBeetle support
pip install bridgebase[redis]         # Redis/Valkey support
pip install bridgebase[all]           # Everything
```

### Requirements

- Python 3.10+
- httpx >= 0.25.0

## Quick Start

### TigerBeetle

```python
from bridgebase import tigerbeetle

# Single import provides BOTH session creation AND type access
with tigerbeetle(jwt_token="your-jwt-token") as tb:
    account = tigerbeetle.Account(
        id=tigerbeetle.id(),
        ledger=1,
        code=1,
        flags=0,
    )
    destination = tigerbeetle.Account(
        id=tigerbeetle.id(),
        ledger=1,
        code=1,
        flags=0,
    )
    tb.create_accounts([account, destination])

    transfer = tigerbeetle.Transfer(
        id=tigerbeetle.id(),
        debit_account_id=account.id,
        credit_account_id=destination.id,
        amount=100,
        ledger=1,
        code=1,
    )
    tb.create_transfers([transfer])
```

### Redis / Valkey

```python
from bridgebase import redis

with redis(jwt_token="your-jwt-token") as rd:
    rd.set("key", "value")
    print(rd.get("key"))
```

## Usage

Use the convenience functions `tigerbeetle()` and `redis()` for the simplest API:

```python
from bridgebase import tigerbeetle, redis

# Context manager (auto cleanup)
with tigerbeetle(jwt_token="your-jwt-token") as tb:
    account = tigerbeetle.Account(
        id=tigerbeetle.id(),
        ledger=1,
        code=1,
    )
    tb.create_accounts([account])

with redis(jwt_token="your-jwt-token") as rd:
    rd.set("key", "value")
```

### Explicit Connect/Close

```python
session = tigerbeetle(jwt_token="your-jwt-token")
try:
    tb = session.connect()
    tb.create_accounts([...])
finally:
    session.close()
```

### TigerBeetle Unified API

The `tigerbeetle` import provides **both** session creation AND access to all TigerBeetle types:

```python
from bridgebase import tigerbeetle

# Use tigerbeetle() to create sessions
with tigerbeetle(jwt_token="...") as tb_client:
    # Use tigerbeetle.* to access TigerBeetle types/functions
    accounts = [
        tigerbeetle.Account(
            id=tigerbeetle.id(),
            ledger=1,
            code="CHECKING",
        ),
        tigerbeetle.Account(
            id=tigerbeetle.id(),
            ledger=1,
            code="SAVINGS",
        ),
    ]
    tb_client.create_accounts(accounts)
    
    # All TigerBeetle types are available:
    # tigerbeetle.Transfer
    # tigerbeetle.AccountFilter
    # tigerbeetle.QueryFilter
    # tigerbeetle.AccountFlags
    # ... and everything else from the native tigerbeetle package
```

**No need to import the native package separately** — everything is available through `bridgebase.tigerbeetle`.

## API Reference

### `tigerbeetle(jwt_token, *, cluster_id=0, api_base_url=...)`

Create a TigerBeetle session.

**Parameters:**
- `jwt_token` (str) — JWT token for authentication
- `cluster_id` (int, optional) — TigerBeetle cluster ID (default: 0)
- `api_base_url` (str, optional) — Override default control-plane URL

**Returns:** `TigerBeetleSession` — Session that returns native `tigerbeetle.ClientSync` via `connect()`

**Example:**
```python
from bridgebase import tigerbeetle

with tigerbeetle(jwt_token="...") as tb:
    tb.create_accounts([...])
```

### `redis(jwt_token, *, db=0, api_base_url=...)`

Create a Redis/Valkey session.

**Parameters:**
- `jwt_token` (str) — JWT token for authentication
- `db` (int, optional) — Redis database index (default: 0)
- `api_base_url` (str, optional) — Override default control-plane URL

**Returns:** `RedisSession` — Session that returns native `redis.Redis` via `connect()`

**Example:**
```python
from bridgebase import redis

with redis(jwt_token="...") as rd:
    rd.set("key", "value")
```

### Session Objects

All sessions (`TigerBeetleSession`, `RedisSession`) share the same interface:

#### `connect() -> NativeClient`

Initialize the session and return the native database client.

1. Resolves gateway endpoint via JWT
2. Opens gateway socket with JWT handshake
3. Starts local proxy on ephemeral port
4. Connects native driver through proxy

#### `close()`

Tear down the session — closes native client, stops proxy, closes gateway socket.

#### Context Manager

```python
with session as client:
    # client is the native library object
    pass
```


### Local Proxy

The SDK starts a local TCP proxy that:
- Binds to ephemeral port (OS-assigned)
- Forwards all traffic bidirectionally between TigerBeetle client and gateway
- Runs in background thread
- Automatically cleaned up on `close()`

## Examples

See the `example.py` files for complete examples.

## Error Handling

The SDK provides custom exceptions:

- `BridgeBaseError` — Base exception
- `AuthError` — JWT authentication failed
- `GatewayError` — Gateway connection failed
- `GatewayResolutionError` — Gateway resolve API call failed (subclass of `GatewayError`)
- `ConnectionError` — Native database connection issues
- `ProxyError` — Local proxy failed to start or forward traffic

```python
from bridgebase import tigerbeetle, AuthError, GatewayResolutionError

try:
    with tigerbeetle(jwt_token="invalid") as tb:
        pass
except AuthError as e:
    print(f"Authentication failed: {e}")
except GatewayResolutionError as e:
    print(f"Gateway resolution failed: {e}")
```

## Development

### Install in editable mode with dev dependencies:

```bash
pip install -e ".[dev]"
```

### Code formatting:

```bash
ruff check bridgebase/
ruff format bridgebase/
```

## Project Structure

```
bridgebase/
├── __init__.py          # Package exports and convenience functions
├── tigerbeetle.py       # TigerBeetle session adapter
├── redis.py             # Redis/Valkey session adapter
├── base.py              # Abstract base session class
├── gateway.py           # Gateway resolver + socket connection
├── proxy.py             # Local TCP proxy
├── credentials.py       # Credential fetching (for future SQL adapters)
└── exceptions.py        # Custom exceptions
```

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
