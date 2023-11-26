from account import (
    AccountList,
    account_lists_years,
    account_list,
    create_new_account_list
)
from verification import (
    VerificationList,
    verification_lists_years,
    verification_list,
    create_new_verification_list
)
from datetime import datetime
import balance


class Year:
    def __init__(self, year: int):
        self._year = year

    def on_first_year(self) -> bool:
        years = verification_lists_years()
        return self._year == years[0]

    def on_last_year(self) -> bool:
        years = verification_lists_years()
        return self._year == years[-1]

    def goto_next_year(self):
        if self.on_last_year():
            print("Already at last year")
            return
        years = verification_lists_years()
        self._year = years[years.index(self._year) + 1]

    def goto_prev_year(self):
        if self.on_first_year():
            print("Already at first year")
            return
        years = verification_lists_years()
        self._year = years[years.index(self._year) - 1]

    def create_new_year(self):
        new_year = verification_lists_years()[-1] + 1
        create_new_verification_list(new_year)
        create_new_account_list(new_year)
        self._year = new_year
        self.verification_list.save_verifications()
        self.account_list.save_accounts()

    def recalc_incoming_account_balances(self):
        years = account_lists_years()
        if years.index(self._year) <= 0:
            print("No previous year, nothing to recalculate")
            return

        # Switch to prev year for easier call of functions
        cur_year_accounts = self.account_list
        self.goto_prev_year()
        prev_year_accounts = self.account_list
        for cur_year_acc in cur_year_accounts:
            prev_year_acc = prev_year_accounts.find_account(cur_year_acc.account_number)
            if prev_year_acc:
                cur_year_acc.incoming_balance = balance.get_balance_for_account(prev_year_acc)
            else:
                cur_year_acc.incoming_balance = 0

        # Switch back to current year
        self.goto_next_year()

    @property
    def year(self) -> int:
        return self._year

    @property
    def verification_list(self) -> VerificationList:
        return verification_list(self._year)

    @property
    def account_list(self) -> AccountList:
        return account_list(self._year)


_year: Year | None = None


def year_init():
    global _year
    if _year is not None:
        raise PermissionError("Year already initialized, not allowed to call again!")

    ver_years = verification_lists_years()
    acc_years = account_lists_years()
    assert ver_years == acc_years, f"Years from verifications are not same as from accounts: {ver_years} {acc_years}"
    years = ver_years

    if years:
        _year = Year(years[-1])
    else:
        cur_year = datetime.now().year
        print(f"No years, create current year: {cur_year}")
        create_new_verification_list(cur_year)
        create_new_account_list(cur_year)
        _year = Year(cur_year)
        _year.verification_list.save_verifications()
        _year.account_list.save_accounts()


def year() -> Year:
    global _year
    assert _year is not None
    return _year
