import dataclasses as dc
import re
from pathlib import Path
import itertools

@dc.dataclass
class Account:
    account_number: int
    description: str

    id: int = dc.field(default_factory=itertools.count().__next__)

ACCOUNT_REGEX = re.compile(r'(\d+), "(.+)"')

def load_accounts(accounts_filename: str) -> list[Account]:
    accounts: list[Account] = []

    print(f"Loading accounts from: {Path(accounts_filename).absolute()}")
    with open(accounts_filename, "r", encoding="utf-8") as ac_file:
        for line in ac_file.readlines():
            match = ACCOUNT_REGEX.match(line)
            if not match:
                continue
            accounts.append(Account(int(match.groups()[0]), match.groups()[1]))

    print(f"Loaded {len(accounts)} accounts")
    return accounts

def find_account(account_num: int | str, accounts: list[Account]) -> Account | None:
    if type(account_num) == str:
        account_num = int(account_num)
    for acc in accounts:
        if acc.account_number == account_num:
            return acc
    return None
