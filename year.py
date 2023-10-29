from verification import (
    VerificationList,
    verification_lists_years,
    verification_list,
    create_new_verification_list
)
from datetime import datetime


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
        self._year = new_year

    @property
    def year(self) -> int:
        return self._year

    @property
    def verification_list(self) -> VerificationList:
        return verification_list(self._year)


_year: Year | None = None


def year_init():
    global _year
    if _year is not None:
        raise PermissionError("Year already initialized, not allowed to call again!")

    years = verification_lists_years()
    if years:
        _year = Year(years[-1])
    else:
        cur_year = datetime.now().year
        print(f"No years, create current year: {cur_year}")
        create_new_verification_list(cur_year)
        _year = Year(cur_year)
        _year.verification_list.save_verifications()


def year() -> Year:
    global _year
    assert _year is not None
    return _year
