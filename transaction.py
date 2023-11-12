import dataclasses as dc

from account import Account

@dc.dataclass
class Transaction:
    account_number: int
    debit: float
    credit: float
    notes: str = ""
