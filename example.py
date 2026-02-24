#!/usr/bin/env python3
"""Example usage of the BridgeBase SDK.

Sessions are lazy — no network calls happen until you call `connect()` or
enter a context manager.  `connect()` returns the native tigerbeetle.ClientSync,
so you get full access to every method the TigerBeetle library provides.
"""

from bridgebase.tigerbeetle import tigerbeetle

JWT = "eyJ..."  # Replace with a real JWT

# ── TigerBeetle (tigerbeetle.ClientSync) ────────────────────────────────
tb_session = tigerbeetle(jwt_token=JWT)
try:
    tb = tb_session.connect()  # returns tigerbeetle.ClientSync
    account = tigerbeetle.Account(
        id=tigerbeetle.id(),
        ledger=1,
        code=1,
        flags=0,
    )
    tb.create_accounts([account])
    print("TB: account created")
finally:
    tb_session.close()

# ── Context-manager style (recommended) ─────────────────────────────────
# __enter__ calls connect() and returns the native client directly.
# __exit__ tears down proxy, gateway socket, and releases credentials.
with tigerbeetle(jwt_token=JWT) as tb:
    account = tigerbeetle.Account(
        id=tigerbeetle.id(),
        ledger=1,
        code=1,
        flags=0,
    )
    tb.create_accounts([account])
    print("TB (ctx): account created")
