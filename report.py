from datetime import date
import dominate
import dominate.tags as dt

from year import Year
from balance import get_balance_for_account, account_has_transactions
from config import config_get_company_name, config_get_company_number


def create_balance_report(filename: str, year: Year, start_date: date=None, end_date: date=None):
    doc = dominate.document(title='ALOP Counting - Balance report')

    if start_date is None:
        start_date = year.period_start
    if end_date is None:
        end_date = year.period_end
    if start_date.year != year.year or end_date.year != year.year:
        raise ValueError("Start or end is not in year")
    if end_date < start_date:
        raise ValueError("End is before start")

    css = """\
body{
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
}

table {
  border-collapse: collapse;
  width: 500pt;
}

th, td {
  padding: 8px;
  min-width: 80pt
}

tr:nth-child(odd) {
    background-color: #f0f0f0;
}
"""

    css_filename = f"{filename}.css"

    with open(css_filename, "w") as css_file:
        css_file.write(css)

    with doc.head:
        dt.link(rel='stylesheet', href=css_filename)
        # dt.script(type='text/javascript', src='script.js')
        pass

    with doc:
        with dt.div(id='header'):
            pass

        with dt.div(style='margin: 50px; font-family: sans-serif; font-size: smaller;'):
            dt.attr(cls='body')
            dt.h1('Balance report')
            dt.h2(config_get_company_name(), style="margin: 4pt 0 4pt 0")
            dt.h2(config_get_company_number(), style="margin: 4pt 0 10pt 0")
            dt.p(f'Accounting year: {year.period_start}  \u2013  {year.period_end}', style="margin: 4pt 0 4pt 0")
            dt.p(f'Period: {start_date}  \u2013  {end_date}', style="margin: 4pt 0 4pt 0")
            dt.p(f'Printed: {date.today()}', style="margin: 4pt 0 4pt 0")
            id = "\u2013" if not year.verification_list.len else str(year.verification_list[-1].id)
            dt.p(f'Last ver. no.: {id}', style="margin: 4pt 0 4pt 0")

            inc_bal_ass_sum = 0
            per_bal_ass_sum = 0
            out_bal_ass_sum = 0
            dt.h2('Assets', style='margin: 40pt 0 0 0')
            with dt.table(style='text-align: right'):
                with dt.tr(style="border-bottom: 2px solid black; background-color: white"):
                    dt.th("")
                    dt.th("Incoming balance")
                    dt.th("Period")
                    dt.th("Outgoing balance")
                for acc in year.account_list:
                    if not (acc.is_asset and (account_has_transactions(acc) or acc.incoming_balance != 0)):
                        continue
                    with dt.tr():
                        acc_bal = get_balance_for_account(acc)
                        dt.td(f"{acc.account_number}  {acc.description}", style='text-align: left')
                        dt.td('{:,.2f}'.format(acc.incoming_balance).replace(',', ' '))
                        dt.td('{:,.2f}'.format(acc_bal - acc.incoming_balance).replace(',', ' '))
                        dt.td('{:,.2f}'.format(acc_bal).replace(',', ' '))
                    inc_bal_ass_sum += acc.incoming_balance
                    per_bal_ass_sum += acc_bal - acc.incoming_balance
                    out_bal_ass_sum += acc_bal
                with dt.tr(style='font-size: medium; border-top: 2px solid black; background-color: white'):
                    dt.th("Sum debts", style='text-align: left')
                    dt.th('{:,.2f}'.format(inc_bal_ass_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(per_bal_ass_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(out_bal_ass_sum).replace(',', ' '))

            inc_bal_deb_sum = 0
            per_bal_deb_sum = 0
            out_bal_deb_sum = 0
            dt.h2('Debts', style='margin: 40pt 0 0 0')
            with dt.table(style='text-align: right'):
                with dt.tr(style="border-bottom: 2px solid black; background-color: white"):
                    dt.th("")
                    dt.th("Incoming balance")
                    dt.th("Period")
                    dt.th("Outgoing balance")
                for acc in year.account_list:
                    if not (acc.is_debt and (account_has_transactions(acc) or acc.incoming_balance != 0)):
                        continue
                    with dt.tr():
                        acc_bal = get_balance_for_account(acc)
                        dt.td(f"{acc.account_number}  {acc.description}", style='text-align: left')
                        dt.td('{:,.2f}'.format(acc.incoming_balance).replace(',', ' '))
                        dt.td('{:,.2f}'.format(acc_bal - acc.incoming_balance).replace(',', ' '))
                        dt.td('{:,.2f}'.format(acc_bal).replace(',', ' '))
                    inc_bal_deb_sum += acc.incoming_balance
                    per_bal_deb_sum += acc_bal - acc.incoming_balance
                    out_bal_deb_sum += acc_bal
                with dt.tr(style='font-size: medium; border-top: 2px solid black; background-color: white'):
                    dt.th("Sum debts", style='text-align: left')
                    dt.th('{:,.2f}'.format(inc_bal_deb_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(per_bal_deb_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(out_bal_deb_sum).replace(',', ' '))

            with dt.table(style='text-align: right; margin-top: 60pt'):
                with dt.tr(style='background-color: white'):
                    dt.th("")
                    dt.th("Incoming balance")
                    dt.th("Period")
                    dt.th("Outgoing balance")
                with dt.tr(style="font-size: large; border-top: 2px solid black; background-color: white"):
                    dt.th("Difference assets and debts", style='text-align: left')
                    dt.th('{:,.2f}'.format(inc_bal_ass_sum - inc_bal_deb_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(per_bal_ass_sum - per_bal_deb_sum).replace(',', ' '))
                    dt.th('{:,.2f}'.format(out_bal_ass_sum - out_bal_deb_sum).replace(',', ' '))

    with open(filename, "w") as html_file:
        html_file.write(str(doc))


def create_result_report(filename: str, year: Year, start_date: date=None, end_date: date=None):
    doc = dominate.document(title='ALOP Counting - Result report')

    if start_date is None:
        start_date = year.period_start
    if end_date is None:
        end_date = year.period_end
    if start_date.year != year.year or end_date.year != year.year:
        raise ValueError("Start or end is not in year")
    if end_date < start_date:
        raise ValueError("End is before start")

    css = """\
body{
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
}

table {
  border-collapse: collapse;
  width: 500pt;
}

th, td {
  padding: 8px;
  min-width: 80pt
}

tr:nth-child(odd) {
    background-color: #f0f0f0;
}
"""

    css_filename = f"{filename}.css"

    with open(css_filename, "w") as css_file:
        css_file.write(css)

    with doc.head:
        dt.link(rel='stylesheet', href=css_filename)
        # dt.script(type='text/javascript', src='script.js')
        pass

    with doc:
        with dt.div(id='header'):
            pass

        with dt.div(style='margin: 50px; font-family: sans-serif; font-size: smaller;'):
            dt.attr(cls='body')
            dt.h1('Result report')
            dt.h2(config_get_company_name(), style="margin: 4pt 0 4pt 0")
            dt.h2(config_get_company_number(), style="margin: 4pt 0 10pt 0")
            dt.p(f'Accounting year: {year.period_start}  \u2013  {year.period_end}', style="margin: 4pt 0 4pt 0")
            dt.p(f'Period: {start_date}  \u2013  {end_date}', style="margin: 4pt 0 4pt 0")
            dt.p(f'Printed: {date.today()}', style="margin: 4pt 0 4pt 0")
            id = "\u2013" if not year.verification_list.len else str(year.verification_list[-1].id)
            dt.p(f'Last ver. no.: {id}', style="margin: 4pt 0 4pt 0")

            per_bal_inc_sum = 0
            dt.h2('Incomes', style='margin: 40pt 0 0 0')
            with dt.table(style='text-align: right'):
                with dt.tr(style="border-bottom: 2px solid black; background-color: white"):
                    dt.th("")
                    dt.th("Period")
                for acc in year.account_list:
                    if not (acc.is_income and account_has_transactions(acc)):
                        continue
                    with dt.tr():
                        acc_bal = get_balance_for_account(acc)
                        dt.td(f"{acc.account_number}  {acc.description}", style='text-align: left')
                        dt.td('{:,.2f}'.format(acc_bal).replace(',', ' '))
                    per_bal_inc_sum += acc_bal
                with dt.tr(style='font-size: medium; border-top: 2px solid black; background-color: white'):
                    dt.th("Sum incomes", style='text-align: left')
                    dt.th('{:,.2f}'.format(per_bal_inc_sum).replace(',', ' '))

            per_bal_cos_sum = 0
            dt.h2('Costs', style='margin: 40pt 0 0 0')
            with dt.table(style='text-align: right'):
                with dt.tr(style="border-bottom: 2px solid black; background-color: white"):
                    dt.th("")
                    dt.th("Period")
                for acc in year.account_list:
                    if not (acc.is_cost and account_has_transactions(acc)):
                        continue
                    with dt.tr():
                        acc_bal = get_balance_for_account(acc)
                        dt.td(f"{acc.account_number}  {acc.description}", style='text-align: left')
                        dt.td('{:,.2f}'.format(acc_bal).replace(',', ' '))
                    per_bal_cos_sum += acc_bal
                with dt.tr(style='font-size: medium; border-top: 2px solid black; background-color: white'):
                    dt.th("Sum costs", style='text-align: left')
                    dt.th('{:,.2f}'.format(per_bal_cos_sum).replace(',', ' '))

            with dt.table(style='text-align: right; margin-top: 60pt'):
                with dt.tr(style='background-color: white'):
                    dt.th("")
                    dt.th("Period")
                with dt.tr(style="font-size: large; border-top: 2px solid black; background-color: white"):
                    dt.th("Calculated result", style='text-align: left')
                    dt.th('{:,.2f}'.format(per_bal_inc_sum - per_bal_cos_sum).replace(',', ' '))

    with open(filename, "w") as html_file:
        html_file.write(str(doc))
