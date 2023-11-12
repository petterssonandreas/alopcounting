import dataclasses as dc
import re
from pathlib import Path
from dataclass_json import dataclass_json_loads, dataclass_json_dumps
from config import config_get_accounts_iterator, config_get_accounts_path


@dc.dataclass
class Account:
    account_number: int
    description: str
    incoming_balance: float = 0

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
    def __init__(self, accounts_filepath: str | Path, year: int, new_year: bool = False):
        self._accounts_filepath = accounts_filepath
        self._year = year
        self._accounts = self._load_accounts(new_year)
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

    def __lt__(self, other):
        return self._year < other._year

    def __lt__(self, other):
        return self._year <= other._year

    def _load_accounts(self, new_year: bool) -> list[Account]:
        acc_file_path = Path(self._accounts_filepath)

        if new_year:
            assert not acc_file_path.exists(), f"{acc_file_path}: already exists"
            acc_file_path.parent.mkdir(exist_ok=True)
            print("Copy accounts from previous year if available")
            years = account_lists_years()
            if len(years):
                self._accounts = account_list(years[-1]).get_accounts()
            else:
                self._accounts = []
            self.save_accounts()
        else:
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

    @property
    def year(self) -> int:
        return self._year

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
        acc_file_path = Path(self._accounts_filepath)
        print(f"Storing accounts in file: {acc_file_path.absolute()}")
        with open(acc_file_path, 'w+', encoding="utf-8") as acc_file:
            print("save accounts")
            acc_file.write(dataclass_json_dumps(self._accounts, indent=4))


_account_lists: list[AccountList] | None = None


def account_list_init():
    global _account_lists
    if _account_lists is None:
        _account_lists = []
    else:
        raise PermissionError("Account list already initialized, not allowed to call again!")

    for al_path in config_get_accounts_iterator():
        al_path = Path(al_path)
        year_dir_name = al_path.parent.name
        try:
            year = int(year_dir_name, 10)
        except ValueError as err:
            print(f"Invalid year, ignoring '{al_path.absolute()}'")
            continue

        print(f"Loading accounts for year {year}")
        _account_lists.append(AccountList(al_path, year))

    _account_lists.sort()


def account_list(year: int) -> AccountList:
    global _account_lists
    assert _account_lists is not None
    for al in _account_lists:
        if year == al.year:
            return al
    raise ValueError(f"Year {year} not present!")


def account_lists_years() -> list[int]:
    global _account_lists
    assert _account_lists is not None
    years: list[int] = []
    for al in _account_lists:
        years.append(al.year)
    return years


def create_new_account_list(year: int):
    global _account_lists
    assert _account_lists is not None
    assert year not in account_lists_years()
    _account_lists.append(AccountList(config_get_accounts_path(year), year, new_year=True))
    _account_lists.sort()
