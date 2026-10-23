import inserts
from db import check_env, connect_with_retry

check_env()
conn = connect_with_retry()
try:
    with conn.cursor() as cur:
        cid = inserts.new_customer(cur)
        aid = inserts.new_account(cur)
        mid = inserts.new_merchant(cur)
        tid = inserts.new_transaction(cur)
        print("ids:", cid, aid, mid, tid)
        cur.execute(
            "select * from banking.transactions where transaction_id = %s", (tid,)
        )
        print(cur.fetchone())
finally:
    conn.rollback()
    conn.close()