import dataclasses as dc
import re
from pathlib import Path
from dataclass_json import dataclass_json_loads, dataclass_json_dumps
from config import config_get_accounts_storage_file_path


@dc.dataclass
class Account:
    account_number: int
    description: str

    @property
    def is_asset(self):
        return 1000 <= self.account_number < 2000

    @property
    def is_debt(self):
        return 2000 <= self.account_number < 3000

    @property
    def is_income(self):
        return 3000 <= self.account_number < 4000

    @property
    def is_cost(self):
        return self.account_number >= 4000

    def __lt__(self, other):
        return self.account_number < other.account_number

    def __lte__(self, other):
        return self.account_number <= other.account_number


class AccountList:
    def __init__(self, accounts_filename: str | Path):
        self._accounts_filename = accounts_filename
        self._accounts = self._load_accounts()
        self._index = 0

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> Account:
        try:
            result = self._accounts[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return result

    def _load_accounts(self) -> list[Account]:
        acc_file_path = Path(self._accounts_filename)

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

    def get_accounts(self) -> list[Account]:
        return self._accounts.copy()

    @property
    def len(self) -> int:
        return len(self._accounts)

    def find_account(self, account_num: int | str) -> Account | None:
        if type(account_num) == str:
            account_num = int(account_num)
        for acc in self:
            if acc.account_number == account_num:
                return acc
        return None

    def add_account(self, account: Account):
        self._accounts.append(account)
        self._accounts.sort()

    def remove_account(self, account: Account):
        self._accounts.remove(account)

    def save_accounts(self):
        acc_file_path = Path(self._accounts_filename)
        print(f"Storing accounts in file: {acc_file_path.absolute()}")
        with open(acc_file_path, 'w', encoding="utf-8") as acc_file:
            acc_file.write(dataclass_json_dumps(self._accounts, indent=4))


_account_list: AccountList | None = None


def account_list_init():
    global _account_list
    _account_list = AccountList(config_get_accounts_storage_file_path())


def account_list() -> AccountList:
    global _account_list
    assert _account_list is not None
    return _account_list
