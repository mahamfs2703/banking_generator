from db import check_env, connect_with_retry

check_env()
conn = connect_with_retry()
with conn, conn.cursor() as cur:
    cur.execute("""
        select table_name, column_name, data_type, is_nullable,
               column_default, is_identity
        from information_schema.columns
        where table_schema = 'banking'
        order by table_name, ordinal_position
    """)
    for row in cur.fetchall():
        print(*row, sep=" | ")

    print()
    cur.execute("select merchant_name, category, city from banking.merchants")
    for row in cur.fetchall():
        print(*row, sep=" | ")

    print()
    cur.execute("select phone, city, country from banking.customers limit 3")
    for row in cur.fetchall():
        print(*row, sep=" | ")
conn.close()