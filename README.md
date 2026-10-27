# banking-generator

Python script that keeps a Postgres OLTP database changing continuously, so a CDC pipeline has inserts, updates and deletes to capture.

Part of a three-repo project:

| Repo | Purpose |
| --- | --- |
| **banking-generator** (this repo) | Simulated banking activity on the source database |
| https://github.com/mahamfs2703/banking-dbt | dbt transformations on Snowflake |
| https://github.com/mahamfs2703/banking_live_dashboard | Streamlit in Snowflake dashboard |

## What it does

Writes to schema `banking` in a Postgres database (Neon) with four tables:

| Table | Notes |
| --- | --- |
| `customers` | `kyc_status`: PENDING, VERIFIED, REJECTED |
| `accounts` | `account_type`: SAVINGS, CHECKING, CREDIT; `status`: ACTIVE, FROZEN, CLOSED; currency default INR |
| `merchants` | name, category, city, country |
| `transactions` | `transaction_type`: PURCHASE, DEPOSIT, WITHDRAWAL, TRANSFER; `status`: PENDING, COMPLETED, FAILED, REVERSED; amount > 0 |

Each table has an `updated_at` column maintained by a trigger.

Event mix (default): **70% inserts, 25% updates, 5% deletes**.

- Inserts mostly add transactions. New customers and accounts are also created, counted within the insert share.
- Updates change transaction statuses and account balances.
- Deletes respect the foreign keys: only leaf rows are removed (transactions, or customers with no accounts).
- Default rate: 2 transactions per minute.
- Stops cleanly on **Ctrl+C**, or after an optional maximum number of minutes. It does not resume automatically.

## Requirements

- Python 3.13 (developed and tested on Windows, in `cmd`)
- Packages: `faker`, `psycopg2`
- A Postgres source with the `banking` schema already created.

## Configuration

Connection settings come from **environment variables**. Never commit credentials.

- Connect to the **direct** Postgres host (no `-pooler` in the hostname). The pooler does not support logical replication, so the pipeline's CDC connection must use the direct host, and the generator should too.

Windows `cmd`:

```bat
python -m venv .venv
.venv\Scripts\activate
set "PGHOST=<host-name>"
set "PGDATABASE=<neon-database-name>"
set "PGUSER=<neon-user-name>"
set "PGPASSWORD=<password>"
```

## Running

```bat
python generator.py --tpm 10 --max-minutes 10
```

Stop with **Ctrl+C**.
