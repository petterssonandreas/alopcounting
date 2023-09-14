
from account import Account, load_accounts
from transaction import Transaction
from verification import Verification, load_verifications, save_verifications

import datetime

def main():
    acc = Account(1920, "Plusgiro")

    # ver = Verification(date=datetime.date(2023, 10, 9))
    # tr = Transaction(acc, 0, 200, "Swish from AP")
    # tr2 = Transaction(acc, 100, 0, "Utbetalning")
    # ver.add_transaction(tr)
    # ver.add_transaction(tr2)
    # ver.save_to_file("myverfile.json")
    # print(ver)
    # ver2 = Verification.load_from_file("myverfile.json")
    # print(ver2)

    accounts = load_accounts("kontoplan.txt")
    verifications = load_verifications("example_verifications")
    save_verifications("example_verifications", verifications)

if __name__ == "__main__":
    main()
