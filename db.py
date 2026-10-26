# db.py is the front door. 
# It checks your PG* environment variables exist, refuses the -pooler host, and connects. 
# If the connection fails, it retries a few times with growing pauses. 
# It reads credentials from environment variables, so the password never sits in a file or on screen.

import os
import sys
import time

import psycopg2

REQUIRED = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]


def check_env():
    missing = [v for v in REQUIRED if not os.environ.get(v)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")
    host = os.environ["PGHOST"]
    if "-pooler" in host:
        sys.exit("PGHOST is the pooled host. Use the direct host.")
    if "://" in host or "@" in host or "/" in host:
        sys.exit("PGHOST must be a bare hostname, not a connection string.")


def connect():
    return psycopg2.connect(
        connect_timeout=10,
        sslmode="require",
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )


def connect_with_retry(max_tries=5):
    delay = 2
    for attempt in range(1, max_tries + 1):
        try:
            return connect()
        except psycopg2.OperationalError:
            if attempt == max_tries:
                raise
            print(f"Connect failed ({attempt}/{max_tries}), retrying in {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 30)
