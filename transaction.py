import dataclasses as dc

from account import Account

@dc.dataclass
class Transaction:
    account: Account
    debit: float
    credit: float
    notes: str = ""
