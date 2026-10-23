import random

from inserts import CITIES


def settle_transaction(cur):
    cur.execute(
        """
        select t.transaction_id, t.transaction_type, t.amount, t.account_id,
               a.account_type, a.balance, a.status
        from banking.transactions t
        join banking.accounts a on a.account_id = t.account_id
        where t.status = 'PENDING'
        order by random() limit 1
        for update of t, a skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    tid, ttype, amount, aid, atype, bal, astatus = row
    outcome = "FAILED" if random.random() < 0.12 else "COMPLETED"
    if outcome == "COMPLETED" and astatus != "ACTIVE":
        outcome = "FAILED"
    if outcome == "COMPLETED" and atype != "CREDIT":
        delta = amount if ttype == "DEPOSIT" else -amount
        if bal + delta < 0:
            outcome = "FAILED"
        else:
            cur.execute(
                "update banking.accounts set balance = balance + %s where account_id = %s",
                (delta, aid),
            )
    cur.execute(
        "update banking.transactions set status = %s where transaction_id = %s",
        (outcome, tid),
    )
    return f"txn {tid} {ttype} PENDING -> {outcome}"


def reverse_transaction(cur):
    cur.execute(
        """
        select t.transaction_id, t.transaction_type, t.amount, t.account_id, a.balance
        from banking.transactions t
        join banking.accounts a on a.account_id = t.account_id
        where t.status = 'COMPLETED' and a.account_type <> 'CREDIT'
        order by random() limit 1
        for update of t, a skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    tid, ttype, amount, aid, bal = row
    delta = -amount if ttype == "DEPOSIT" else amount
    if bal + delta < 0:
        return None
    cur.execute(
        "update banking.accounts set balance = balance + %s where account_id = %s",
        (delta, aid),
    )
    cur.execute(
        "update banking.transactions set status = 'REVERSED' where transaction_id = %s",
        (tid,),
    )
    return f"txn {tid} {ttype} COMPLETED -> REVERSED"


def change_account_status(cur):
    cur.execute(
        """
        select account_id, status from banking.accounts
        where status <> 'CLOSED'
        order by random() limit 1
        for update skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    aid, status = row
    if status == "ACTIVE":
        new = random.choices(["FROZEN", "CLOSED"], weights=[95, 5])[0]
    else:
        new = random.choices(["ACTIVE", "CLOSED"], weights=[90, 10])[0]
    cur.execute(
        "update banking.accounts set status = %s where account_id = %s", (new, aid)
    )
    return f"account {aid} {status} -> {new}"


def update_kyc(cur):
    cur.execute(
        """
        select customer_id from banking.customers
        where kyc_status = 'PENDING'
        order by random() limit 1
        for update skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    new = random.choices(["VERIFIED", "REJECTED"], weights=[85, 15])[0]
    cur.execute(
        "update banking.customers set kyc_status = %s where customer_id = %s",
        (new, row[0]),
    )
    return f"customer {row[0]} KYC PENDING -> {new}"


def change_city(cur):
    cur.execute(
        """
        select customer_id, city from banking.customers
        order by random() limit 1
        for update skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    cid, old = row
    new = random.choice([c for c in CITIES if c != old])
    cur.execute(
        "update banking.customers set city = %s where customer_id = %s", (new, cid)
    )
    return f"customer {cid} city {old} -> {new}"


def delete_failed_transaction(cur):
    cur.execute(
        """
        select transaction_id from banking.transactions
        where status = 'FAILED'
        order by random() limit 1
        for update skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    cur.execute(
        "delete from banking.transactions where transaction_id = %s", (row[0],)
    )
    return f"deleted txn {row[0]}"


def delete_orphan_customer(cur):
    cur.execute(
        """
        select c.customer_id from banking.customers c
        where not exists (
            select 1 from banking.accounts a where a.customer_id = c.customer_id
        )
        order by random() limit 1
        for update skip locked
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    cur.execute("delete from banking.customers where customer_id = %s", (row[0],))
    return f"deleted customer {row[0]}"