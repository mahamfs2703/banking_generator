import random
from decimal import Decimal

from faker import Faker

fake = Faker("en_IN")

CITIES = [
    "Pune", "Mumbai", "Delhi", "Chennai", "Bengaluru", "Hyderabad",
    "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Nagpur", "Indore",
]
MERCHANT_CATEGORIES = ["GROCERY", "FUEL", "FOOD", "ELECTRONICS"]
ACCOUNT_TYPES = ["SAVINGS", "CHECKING", "CREDIT"]
TXN_TYPES = ["PURCHASE", "DEPOSIT", "WITHDRAWAL", "TRANSFER"]
TXN_WEIGHTS = [60, 15, 10, 15]


def money(x):
    return Decimal(str(round(x, 2)))


def new_customer(cur):
    first = fake.first_name().replace(" ", "")
    last = fake.last_name().replace(" ", "")
    email = f"{first}.{last}{random.randint(100, 99999)}@example.com".lower()
    phone = str(random.randint(6, 9)) + "".join(random.choices("0123456789", k=9))
    cur.execute(
        """
        insert into banking.customers (first_name, last_name, email, phone, city, country)
        values (%s, %s, %s, %s, %s, 'India')
        on conflict (email) do nothing
        returning customer_id
        """,
        (first, last, email, phone, random.choice(CITIES)),
    )
    row = cur.fetchone()
    return row[0] if row else None


def new_account(cur):
    cur.execute(
        "select customer_id from banking.customers "
        "where kyc_status <> 'REJECTED' order by random() limit 1"
    )
    row = cur.fetchone()
    if not row:
        return None
    acc_type = random.choices(ACCOUNT_TYPES, weights=[50, 35, 15])[0]
    balance = 0 if acc_type == "CREDIT" else money(random.uniform(1000, 200000))
    cur.execute(
        """
        insert into banking.accounts (customer_id, account_type, balance)
        values (%s, %s, %s)
        returning account_id
        """,
        (row[0], acc_type, balance),
    )
    return cur.fetchone()[0]


def new_merchant(cur):
    cur.execute(
        """
        insert into banking.merchants (merchant_name, category, city, country)
        values (%s, %s, %s, 'India')
        returning merchant_id
        """,
        (fake.company(), random.choice(MERCHANT_CATEGORIES), random.choice(CITIES)),
    )
    return cur.fetchone()[0]


def pick_amount(ttype):
    if ttype == "PURCHASE":
        x = random.lognormvariate(6.5, 1.0)
    elif ttype == "DEPOSIT":
        x = random.lognormvariate(8.5, 0.8)
    elif ttype == "WITHDRAWAL":
        x = random.choice(range(500, 20001, 500))
    else:
        x = random.lognormvariate(8.0, 1.0)
    return money(max(10, min(x, 200000)))


def new_transaction(cur):
    cur.execute(
        "select account_id from banking.accounts "
        "where status = 'ACTIVE' order by random() limit 1"
    )
    acc = cur.fetchone()
    if not acc:
        return None
    ttype = random.choices(TXN_TYPES, weights=TXN_WEIGHTS)[0]
    merchant_id = None
    if ttype == "PURCHASE":
        cur.execute("select merchant_id from banking.merchants order by random() limit 1")
        m = cur.fetchone()
        merchant_id = m[0] if m else None
    cur.execute(
        """
        insert into banking.transactions
            (account_id, merchant_id, transaction_type, amount)
        values (%s, %s, %s, %s)
        returning transaction_id
        """,
        (acc[0], merchant_id, ttype, pick_amount(ttype)),
    )
    return cur.fetchone()[0]