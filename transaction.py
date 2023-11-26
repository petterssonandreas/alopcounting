import dataclasses as dc

@dc.dataclass
class Transaction:
    account_number: int
    debit: float
    credit: float
    notes: str = ""
