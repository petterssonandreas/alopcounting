import dataclasses as dc
from account import Account, account_list
from verification import Verification, verification_list
from transaction import Transaction

def get_transactions_for_account(account: Account) -> list[tuple[Transaction, Verification]]:
    return [(trans, ver) for ver in verification_list for trans in ver.transactions if account == trans.account]

# def get_balance_for_account(account: Account) -> float:
#     balance = 0.0
#     for ver in verification_list:


