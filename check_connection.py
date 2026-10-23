import os
import sys
import psycopg2

REQUIRED = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]
missing = [v for v in REQUIRED if not os.environ.get(v)]
if missing:
    sys.exit(f"Missing env vars: {', '.join(missing)}")
if "-pooler" in os.environ["PGHOST"]:
    sys.exit("PGHOST is the pooled host. Use the direct host.")

conn = psycopg2.connect(connect_timeout=10, sslmode="require")
with conn, conn.cursor() as cur:
    cur.execute("select current_user, current_database()")
    print("Connected as:", *cur.fetchone())
    for t in ("customers", "accounts", "merchants", "transactions"):
        cur.execute(f"select count(*) from banking.{t}")
        print(t,cur.fetchone()[0])
conn.close()