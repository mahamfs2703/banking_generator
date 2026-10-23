import changes
import inserts
from db import check_env, connect_with_retry

check_env()
conn = connect_with_retry()
try:
    with conn.cursor() as cur:
        for _ in range(3):
            inserts.new_customer(cur)
            inserts.new_account(cur)
            inserts.new_transaction(cur)
        funcs = [
            changes.settle_transaction,
            changes.reverse_transaction,
            changes.change_account_status,
            changes.update_kyc,
            changes.change_city,
            changes.delete_failed_transaction,
            changes.delete_orphan_customer,
        ]
        for f in funcs:
            for _ in range(3):
                print(f.__name__, "->", f(cur))
finally:
    conn.rollback()
    conn.close()