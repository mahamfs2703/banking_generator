# generator.py is the manager. It runs a loop forever: pick an event, run it, commit, sleep, repeat.

import argparse
import random
import sys
import time
from collections import Counter

import psycopg2

import changes
import inserts
from db import check_env, connect_with_retry

SETTLE_BATCH = 4
MIN_MERCHANTS = 12
MAX_CONSECUTIVE_ERRORS = 10
TXN_FRACTION = 0.70 * 0.90  # share of events that are new transactions


def settle_batch(cur):
    done = [changes.settle_transaction(cur) for _ in range(SETTLE_BATCH)]
    done = [d for d in done if d]
    return f"settled {len(done)} txns" if done else None


# (name, function, weight). Weights add up to 100: 70 insert, 25 update, 5 delete.
EVENTS = [
    ("new_transaction", inserts.new_transaction, 63),
    ("new_account", inserts.new_account, 4.9),
    ("new_customer", inserts.new_customer, 2.1),
    ("settle", settle_batch, 15),
    ("reverse", changes.reverse_transaction, 1.25),
    ("account_status", changes.change_account_status, 2.5),
    ("kyc", changes.update_kyc, 3.75),
    ("city", changes.change_city, 2.5),
    ("delete_failed_txn", changes.delete_failed_transaction, 3),
    ("delete_orphan_customer", changes.delete_orphan_customer, 2),
]
WEIGHTS = [e[2] for e in EVENTS]


def ensure_merchants(conn):
    with conn, conn.cursor() as cur:
        cur.execute("select count(*) from banking.merchants")
        missing = max(0, MIN_MERCHANTS - cur.fetchone()[0])
        for _ in range(missing):
            inserts.new_merchant(cur)
    return missing


def safe_close(conn):
    try:
        conn.close()
    except Exception:
        pass


def run(args):
    mean_gap = 60.0 / (args.tpm / TXN_FRACTION)
    deadline = (
        time.monotonic() + args.max_minutes * 60 if args.max_minutes else None
    )
    conn = connect_with_retry()
    added = ensure_merchants(conn)
    print(
        f"Started: {args.tpm} txn/min, one event about every {mean_gap:.1f}s, "
        f"{added} merchants added. Ctrl+C to stop."
    )
    counts = Counter()
    errors = 0
    try:
        while deadline is None or time.monotonic() < deadline:
            name, func, _ = random.choices(EVENTS, weights=WEIGHTS)[0]
            try:
                with conn.cursor() as cur:
                    result = func(cur)
                conn.commit()
                counts[name if result else name + " (skipped)"] += 1
                errors = 0
                print(f"{time.strftime('%H:%M:%S')} {name}: {result}")
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                errors += 1
                print("Connection lost, reconnecting...")
                safe_close(conn)
                conn = connect_with_retry()
            except psycopg2.Error as e:
                errors += 1
                conn.rollback()
                print(f"{name} failed: {type(e).__name__} {e.pgcode}")
            if errors >= MAX_CONSECUTIVE_ERRORS:
                print("Too many consecutive errors, stopping.")
                break
            gap = min(random.expovariate(1.0 / mean_gap), mean_gap * 4)
            if deadline is not None:
                gap = min(gap, max(0.0, deadline - time.monotonic()))
            time.sleep(gap)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        safe_close(conn)
        print("Summary:")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tpm", type=float, default=2.0,
                    help="new transactions per minute (default 2)")
    ap.add_argument("--max-minutes", type=float, default=None,
                    help="stop on its own after this many minutes")
    args = ap.parse_args()
    if args.tpm <= 0:
        sys.exit("--tpm must be greater than 0")
    check_env()
    try:
        run(args)
    except psycopg2.OperationalError:
        sys.exit("Could not reach the database after retries.")


if __name__ == "__main__":
    main()
