import dataclasses as dc
import datetime
from pathlib import Path
import re
import os

from config import config_get_verifications_dir_iterator, config_get_verifications_dir_path
from dataclass_json import dataclass_json_dumps, dataclass_json_loads
from transaction import Transaction


@dc.dataclass
class Verification:
    id: int
    date: datetime.date = dc.field(default_factory=datetime.date.today)
    transactions: list[Transaction] = dc.field(default_factory=list)
    notes: str = ""
    discarded: bool = False

    @classmethod
    def load_from_file(cls, filename: str | Path):
        with open(filename, "r", encoding="utf-8") as verfile:
            ver = dataclass_json_loads(verfile.read())
        return ver

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def save_to_file(self, dir: Path):
        filename = f"verification_{self.date}_{self.id}.json"
        with open(dir / filename, "w", encoding="utf-8") as verfile:
            verfile.write(dataclass_json_dumps(self, indent=4))

    def __lt__(self, other):
        return self.id < other.id

    def __lte__(self, other):
        return self.id <= other.id


class VerificationList:
    def __init__(self, verifications_dir: str | Path | None, year: int):
        self._index = 0
        self._year = year
        self._verifications_dir = verifications_dir
        self._verifications = self._load_verifications()
        self._year_closed = False

    def __lt__(self, other):
        return self._year < other._year

    def __lte__(self, other):
        return self._year <= other._year

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> Verification:
        try:
            result = self._verifications[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return result

    def __len__(self) -> int:
        return len(self._verifications)

    def __getitem__(self, idx) -> Verification:
        if type(idx) is not int:
            raise TypeError
        if idx < 0:
            idx = -idx - 1
            vers_copy = self._verifications.copy()
            vers_copy.reverse()
            return vers_copy[idx]
        return self._verifications[idx]

    def _load_verifications(self) -> list[Verification]:
        verifications: list[Verification] = []

        dir = Path(self._verifications_dir)
        if not dir.exists():
            print(f"No dir '{dir}', ignore loading verifications")
            return verifications

        assert dir.is_dir(), f"{dir}: not a directory"
        print(f"Loading verifications from: {dir.absolute()}")
        for filepath in dir.iterdir():
            if "verification" in filepath.name:
                verifications.append(Verification.load_from_file(filepath))

        verifications.sort()

        print(f"Loaded {len(verifications)} verifications")
        return verifications

    def get_verifications(self) -> list[Verification]:
        return self._verifications.copy()

    def get_verification_at(self, index: int) -> Verification:
        return self._verifications[index]

    @property
    def len(self) -> int:
        return len(self._verifications)

    @property
    def year(self) -> int:
        return self._year

    @property
    def year_closed(self) -> bool:
        return self._year_closed

    def close_year(self):
        if self._year_closed:
            print(f"Year {self._year} already closed")
        self._year_closed = True

    def open_year(self):
        if not self._year_closed:
            print(f"Year {self._year} already open")
        self._year_closed = False

    def find_verification(self, id: int | str) -> Verification | None:
        if type(id) == str:
            id = int(id)
        for ver in self:
            if ver.id == id:
                return ver
        return None

    def add_verification(self, verification: Verification):
        self._verifications.append(verification)

    def remove_verification(self, verification: Verification):
        self._verifications.remove(verification)

    def save_verifications(self):
        dir = Path(self._verifications_dir)
        if dir.exists():
            assert dir.is_dir(), f"{dir}: not a directory"
        else:
            os.mkdir(dir.absolute())

        print(f"Using verifications directory: {dir.absolute()}")
        for filepath in dir.iterdir():
            if "verification" in filepath.name:
                filepath.unlink()
        for ver in self:
            ver.save_to_file(dir)


_verification_lists: list[VerificationList] | None = None


def verification_list_init():
    global _verification_lists
    if _verification_lists is None:
        _verification_lists = []
    else:
        raise PermissionError("Verification list already initialized, not allowed to call again!")

    for vl_path in config_get_verifications_dir_iterator():
        vl_path = Path(vl_path)
        if not vl_path.is_dir():
            print(f"{vl_path} is not a directory, ignoring for ver loading")
            continue

        year_dir_name = vl_path.name
        try:
            year = int(year_dir_name, 10)
        except ValueError as err:
            print(f"Invalid year, ignoring '{vl_path.absolute()}'")
            continue

        print(f"Loading verifications for year {year}")
        _verification_lists.append(VerificationList(vl_path, year))

    _verification_lists.sort()


def verification_list(year: int) -> VerificationList:
    global _verification_lists
    assert _verification_lists is not None
    for vl in _verification_lists:
        if year == vl.year:
            return vl
    raise ValueError(f"Year {year} not present!")


def verification_lists_years() -> list[int]:
    global _verification_lists
    assert _verification_lists is not None
    years: list[int] = []
    for vl in _verification_lists:
        years.append(vl.year)
    return years


def create_new_verification_list(year: int):
    global _verification_lists
    assert _verification_lists is not None
    assert year not in verification_lists_years()
    dir = config_get_verifications_dir_path(year)
    _verification_lists.append(VerificationList(dir, year))
    _verification_lists.sort()
