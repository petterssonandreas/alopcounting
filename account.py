import dataclasses as dc
import re
from pathlib import Path
from dataclass_json import dataclass_json_loads, dataclass_json_dumps

@dc.dataclass
class Account:
    account_number: int
    description: str

    def __lt__(self, other):
        return self.account_number < other.account_number

    def __lte__(self, other):
        return self.account_number <= other.account_number

ACCOUNT_REGEX = re.compile(r'(\d+), "(.+)"')

def load_accounts(accounts_file: str) -> list[Account]:
    acc_file_path = Path(accounts_file)

    assert acc_file_path.exists(), f"{acc_file_path}: no such path"

    print(f"Loading accounts from: {acc_file_path.absolute()}")
    with open(acc_file_path, 'r', encoding='utf-8') as acc_file:
        accounts = dataclass_json_loads(acc_file.read())

    print(f"Loaded {len(accounts)} accounts")
    accounts.sort()
    filtered_accounts = []
    for idx, acc in enumerate(accounts):
        if idx > 0 and accounts[idx - 1].account_number == acc.account_number:
            print(f"Found account with account number duplicate on index {idx}, removing: {acc}")
        else:
            filtered_accounts.append(acc)

    print(f"{len(filtered_accounts)} accounts left after filtering")
    return filtered_accounts

def find_account(account_num: int | str, accounts: list[Account]) -> Account | None:
    if type(account_num) == str:
        account_num = int(account_num)
    for acc in accounts:
        if acc.account_number == account_num:
            return acc
    return None

def save_accounts(accounts_file: str, accounts: list[Account]):
    acc_file_path = Path(accounts_file)
    print(f"Storing accounts in file: {acc_file_path.absolute()}")
    with open(acc_file_path, 'w', encoding="utf-8") as acc_file:
        acc_file.write(dataclass_json_dumps(accounts, indent=4))
