import dataclasses as dc
import json
import datetime
from pathlib import Path
import itertools

from dataclass_json import dataclass_json_dumps, dataclass_json_loads
from transaction import Transaction

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dc.is_dataclass(o):
            return dc.asdict(o)
        return super().default(o)

@dc.dataclass
class Datetime:
    year: int
    month: int
    day: int

@dc.dataclass
class Verification:
    id: int
    date: datetime.date = dc.field(default_factory=datetime.date.today)
    transactions: list[Transaction] = dc.field(default_factory=list)
    notes: str = ""
    discarded: bool = False

    @classmethod
    def load_from_file(cls, filename: str | Path):
        with open(filename, "r") as verfile:
            ver = dataclass_json_loads(verfile.read())
        return ver

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def save_to_file(self, dir: Path):
        filename = f"verification_{self.date}_{self.id}.json"
        with open(dir / filename, "w") as verfile:
            verfile.write(dataclass_json_dumps(self, indent=4))

    def __lt__(self, other):
        return self.id < other.id

    def __lte__(self, other):
        return self.id <= other.id

def load_verifications(verifications_dir: str) -> list[Verification]:
    verifications: list[Verification] = []

    dir = Path(verifications_dir)
    assert dir.exists(), f"{dir}: no such path"
    assert dir.is_dir(), f"{dir}: not a directory"

    print(f"Loading verifications from: {dir.absolute()}")
    for filepath in dir.iterdir():
        verifications.append(Verification.load_from_file(filepath))

    verifications.sort()

    print(f"Loaded {len(verifications)} verifications")
    return verifications

def save_verifications(verifications_dir: str, verifications: list[Verification]):
    dir = Path(verifications_dir)
    assert dir.exists(), f"{dir}: no such path"
    assert dir.is_dir(), f"{dir}: not a directory"

    print(f"Using verifications directory: {dir.absolute()}")
    for filepath in dir.iterdir():
        filepath.unlink()
    for ver in verifications:
        ver.save_to_file(dir)

def save_verification(verifications_dir: str, verification: Verification):
    dir = Path(verifications_dir)
    assert dir.exists(), f"{dir}: no such path"
    assert dir.is_dir(), f"{dir}: not a directory"

    print(f"Using verifications directory: {dir.absolute()}")
    verification.save_to_file(dir)
