from account import Account
from verification import Verification
from transaction import Transaction
from year import year

def get_transactions_for_account(account: Account) -> list[tuple[Transaction, Verification]]:
    return [(trans, ver) for ver in year().verification_list for trans in ver.transactions if account == trans.account]

def get_balance_from_transactions(account: Account, transactions: list[Transaction]) -> float:
    balance = 0.0
    for trans in transactions:
        balance += trans.debit - trans.credit
    if account.is_debt or account.is_income:
        # Debt or income account, flip sign
        balance = -balance
    return balance

def get_balance_for_account(account: Account) -> float:
    return get_balance_from_transactions(account, [t for t, _ in get_transactions_for_account(account)])
