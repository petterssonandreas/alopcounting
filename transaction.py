import dataclasses as dc

from account import Account

@dc.dataclass
class Transaction:
    account: Account
    credit: float
    debit: float
    notes: str = ""
