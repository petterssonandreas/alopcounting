import dataclasses as dc
import datetime
from pathlib import Path

from config import config_get_verifications_storage_dir_path
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
    def __init__(self, verifications_dir: str | Path):
        self._verifications_dir = verifications_dir
        self._verifications = self._load_verifications()
        self._index = 0

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

    def _load_verifications(self) -> list[Verification]:
        verifications: list[Verification] = []

        dir = Path(self._verifications_dir)
        assert dir.exists(), f"{dir}: no such path"
        assert dir.is_dir(), f"{dir}: not a directory"

        print(f"Loading verifications from: {dir.absolute()}")
        for filepath in dir.iterdir():
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
        assert dir.exists(), f"{dir}: no such path"
        assert dir.is_dir(), f"{dir}: not a directory"

        print(f"Using verifications directory: {dir.absolute()}")
        for filepath in dir.iterdir():
            filepath.unlink()
        for ver in self:
            ver.save_to_file(dir)


_verification_list: VerificationList | None = None


def verification_list_init():
    global _verification_list
    _verification_list = VerificationList(config_get_verifications_storage_dir_path())


def verification_list() -> VerificationList:
    global _verification_list
    assert _verification_list is not None
    return _verification_list
