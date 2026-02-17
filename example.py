#!/usr/bin/env python3
"""Example usage of the BridgeBase SDK.

Sessions are lazy — no network calls happen until you call `connect()` or
enter a context manager.  `connect()` returns the *native* database client,
so you get full access to every method the underlying library provides.
"""

from bridgebase import Client

JWT = "eyJ..."  # Replace with a real JWT

sdk = Client(region="ap-south-1")

# ── PostgreSQL (psycopg2 connection) ─────────────────────────────────────
pg_session = sdk.pg(jwt_token=JWT, database="app")
try:
    conn = pg_session.connect()       # returns psycopg2 connection
    cur = conn.cursor()
    cur.execute("SELECT now()")
    print("PG:", cur.fetchone())
    cur.close()
finally:
    pg_session.close()

# ── MySQL (pymysql connection) ───────────────────────────────────────────
my_session = sdk.my(jwt_token=JWT, database="app")
try:
    conn = my_session.connect()       # returns pymysql connection
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        print("MY:", cur.fetchone())
finally:
    my_session.close()

# ── Redis (redis.Redis client) ──────────────────────────────────────────
rd_session = sdk.rd(jwt_token=JWT)
try:
    r = rd_session.connect()          # returns redis.Redis instance
    r.set("hello", "world")
    print("RD:", r.get("hello"))
finally:
    rd_session.close()

# ── ClickHouse (clickhouse_driver.Client) ────────────────────────────────
ch_session = sdk.ch(jwt_token=JWT, database="analytics")
try:
    client = ch_session.connect()     # returns clickhouse_driver.Client
    result = client.execute("SELECT 1")
    print("CH:", result)
finally:
    ch_session.close()

# ── TigerBeetle (tigerbeetle.ClientSync) ────────────────────────────────
import tigerbeetle

tb_session = sdk.tb(jwt_token=JWT)
try:
    tb = tb_session.connect()         # returns tigerbeetle.ClientSync
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
with sdk.pg(jwt_token=JWT, database="app") as conn:
    cur = conn.cursor()
    cur.execute("SELECT 1 + 1 AS answer")
    print("PG (ctx):", cur.fetchone())
    cur.close()
