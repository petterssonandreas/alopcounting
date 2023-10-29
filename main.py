
import re
from typing import Any
from account import Account, account_list, account_list_init
from transaction import Transaction
from verification import Verification, verification_list_init
from balance import get_transactions_for_account, get_balance_for_account, get_balance_from_transactions
from config import config_init, config_do_git_commit
from year import year_init, year
import PySimpleGUI as sg
import pprint
import dataclasses as dc
import dominate
import dominate.tags as dt
import webbrowser
from _version import __version__
from datetime import date

@dc.dataclass
class ColInfo:
    name: str
    size: tuple[int, int]


COLS = {
    "acc": ColInfo("Account", (10, 1)),
    "des": ColInfo("Description", (30, 1)),
    "deb": ColInfo("Debit", (10, 1)),
    "cre": ColInfo("Credit", (10, 1)),
    "not": ColInfo("Notes", (50, 1)),
}
MAX_ROWS = 20


def populate_verification_layout(window: sg.Window, current_ver_idx: int):
    ver = year().verification_list.get_verification_at(current_ver_idx)
    window["ver_id"].update(ver.id)
    window["ver_date"].update(ver.date)

    if current_ver_idx == 0:
        window['prev'].update(disabled=True)
    else:
        window['prev'].update(disabled=False)
    if current_ver_idx == (year().verification_list.len - 1):
        window['next'].update(disabled=True)
    else:
        window['next'].update(disabled=False)

    # Clear table
    # NOTE: need to set visible from left to right, i.e. idx first
    num_rows = len(ver.transactions)
    [window[f"row{row}_idx"].update(visible=(row < num_rows)) for row in range(MAX_ROWS)]
    [window[f"row{row}_{col}"].update('', visible=(row < num_rows)) for col in COLS.keys() for row in range(MAX_ROWS)]
    [window[f"row{row}_delete"].update(visible=(row < num_rows)) for row in range(MAX_ROWS)]

    for i, trans in enumerate(ver.transactions):
        window[f"row{i}_acc"].update(trans.account.account_number)
        window[f"row{i}_des"].update(trans.account.description)
        window[f"row{i}_deb"].update(trans.debit)
        window[f"row{i}_cre"].update(trans.credit)
        window[f"row{i}_not"].update(trans.notes)

    tot_deb = 0
    tot_cre = 0
    [(tot_deb := tot_deb + t.debit, tot_cre := tot_cre + t.credit) for t in ver.transactions]
    window["accumulate_deb"].update(tot_deb)
    window["accumulate_cre"].update(tot_cre)
    diff = round(tot_deb - tot_cre, ndigits=2)
    window["accumulate_diff"].update(diff)


def get_transactions_from_layout(values: dict[str: str]) -> list[Transaction] | None:
    rows_dict = {row: {k: v for k, v in values.items() if f"row{row}_" in k} for row in range(MAX_ROWS)}
    new_transes = []
    for row, vals in rows_dict.items():
        if not vals[f"row{row}_acc"]:
            continue

        debit = 0.0
        credit = 0.0

        acc_val = vals[f"row{row}_acc"]
        acc = account_list().find_account(acc_val)
        if not acc:
            sg.popup(f"Row {row}: No account with number '{acc_val}'!")
            return None
        try:
            debit = round(float(str(vals[f"row{row}_deb"]).replace(",", ".")), ndigits=2)
        except ValueError:
            if vals[f"row{row}_deb"]:
                sg.popup(f"Row {row}: Bad debet, not a number!")
                return None
        try:
            credit = round(float(str(vals[f"row{row}_cre"]).replace(",", ".")), ndigits=2)
        except ValueError:
            if vals[f"row{row}_cre"]:
                sg.popup(f"Row {row}: Bad kredit, not a number!")
                return None

        if credit and debit:
            sg.popup(f"Row {row}: Both kredit and debet cannot be set!")
            return None

        new_transes.append(Transaction(acc, debit, credit, vals[f"row{row}_not"]))

    return new_transes


def store_verification_from_layout(verification: Verification, values: dict[str: str]) -> bool:
    new_transes = get_transactions_from_layout(values)
    if new_transes is None:
        return False
    verification.transactions = new_transes
    pprint.pprint(new_transes, indent=4)
    return True


def cmp_verification_and_layout(verification: Verification, values: dict[str: str]) -> bool:
    new_transes = get_transactions_from_layout(values)
    if new_transes is None:
        return False
    if len(verification.transactions) != len(new_transes):
        return False
    for ver_trans, new_trans in zip(verification.transactions, new_transes):
        if ver_trans != new_trans:
            return False
    return True


def alternative_background_color() -> str:
    bg = int(sg.theme_background_color()[1:], base=16)
    alt_bg = bg + 0x101010
    return f"#{hex(alt_bg)[2:]}"


def get_column_layout() -> list[list[Any]]:
    header = sg.Column([[
        sg.Text("", size=(4, 1)),
        sg.Text(COLS["acc"].name, justification='left', size=COLS["acc"].size[0] + 1, pad=(1,1), border_width=0,),
        sg.Text(COLS["des"].name, justification='left', size=COLS["des"].size[0], pad=(1,1), border_width=0,),
        sg.Text(COLS["deb"].name, justification='left', size=COLS["deb"].size[0] - 2, pad=(1,1), border_width=0,),
        sg.Text(COLS["cre"].name, justification='left', size=COLS["cre"].size[0] - 1, pad=(1,1), border_width=0,),
        sg.Text(COLS["not"].name, justification='left', size=COLS["not"].size[0] - 4, pad=(1,1), border_width=0,),
        sg.Text("", size=(3, 0)),
    ], [sg.HorizontalSeparator()]])

    column_layout = []
    for row in range(MAX_ROWS):
        color = alternative_background_color() if row % 2 else sg.theme_background_color()
        column_layout += [[sg.Column([[
            sg.Text(str(row), size=(4, 1), justification='right', key=f"row{row}_idx", background_color=color),
            sg.Combo(values=[acc.account_number for acc in account_list()], size=COLS["acc"].size, pad=(1,1), key=f"row{row}_acc"),
            sg.Text(size=COLS["des"].size, pad=(1,1), border_width=0, justification='left', key=f"row{row}_des", background_color=color),
            sg.InputText(size=COLS["deb"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_deb"),
            sg.InputText(size=COLS["cre"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_cre"),
            sg.InputText(size=COLS["not"].size, pad=(1,1), border_width=0, justification='left', key=f"row{row}_not"),
            sg.Button("X", key=f"row{row}_delete", pad=(3, 0)),
        ]], background_color=color)]]

    return [header], [sg.Column(column_layout, scrollable=True, vertical_scroll_only=True, size=(1000, 300), key="ver_col")]


def get_accumulation_layout() -> list[list[Any]]:
    return [[
        sg.Text("", size=(4, 1)),
        sg.Text("", justification='left', size=COLS["acc"].size[0] + 1, pad=(1,1), border_width=0,),
        sg.Text("", justification='left', size=COLS["des"].size[0], pad=(1,1), border_width=0,),
        sg.Text("", key="accumulate_deb", justification='right', size=COLS["deb"].size[0] - 2, pad=(1,1), border_width=0,),
        sg.Text("", key="accumulate_cre", justification='right', size=COLS["cre"].size[0] - 1, pad=(1,1), border_width=0,),
        sg.Text("Diff:", justification='right', size=COLS["not"].size[0] - 4, pad=(1,1), border_width=0,),
        sg.Text("", size=(6, 1), justification="right", key="accumulate_diff"),
    ]]


def get_accounts_column_layout() -> list[list[Any]]:
    header = sg.Column([[
        sg.Text("", size=(4, 1)),
        sg.Text("Account", justification='left', size=(6, 1), pad=(1,1), border_width=0,),
        sg.Text("Description", justification='left', size=(60, 1), pad=(1,1), border_width=0,),
        sg.Text("Balance", justification='left', size=(10, 1), pad=(1,1), border_width=0,),
        sg.Text("", size=(15, 0)),
        sg.Text("", size=(3, 0)),
    ], [sg.HorizontalSeparator()]])

    column_layout = []
    for row, acc in enumerate(account_list()):
        color = alternative_background_color() if row % 2 else sg.theme_background_color()
        column_layout += [[sg.Column([[
            sg.Text("", size=(4, 1), background_color=color),
            sg.Text(acc.account_number, justification='left', size=(6, 1), pad=(1,1), border_width=0, background_color=color),
            sg.Text(acc.description, justification='left', size=(60, 1), pad=(1,1), border_width=0, background_color=color),
            sg.Text(get_balance_for_account(acc), justification='right', size=(10, 1), pad=(1,4), border_width=0, background_color=color),
            sg.Button("Transactions", key=f"row{row}_acc_show_transactions", pad=(15, 0)),
            sg.Button("X", key=f"row{row}_delete_acc", pad=(3, 0)),
        ]], background_color=color)]]

    return [header], [sg.Column(column_layout, scrollable=True, vertical_scroll_only=True, size=(800, 400), key="acc_col")]


def get_account_transactions_column_layout(account: Account) -> list[list[Any]]:
    header = sg.Column([[
        sg.Text("", size=(4, 1)),
        sg.Text("Verification", justification='left', size=(15, 1), pad=(1,1), border_width=0,),
        sg.Text("Date", justification='left', size=(15, 1), pad=(1,1), border_width=0,),
        sg.Text(COLS["deb"].name, justification='left', size=COLS["deb"].size[0], pad=(3,1), border_width=0,),
        sg.Text(COLS["cre"].name, justification='left', size=COLS["cre"].size[0], pad=(3,1), border_width=0,),
        sg.Text("Balance", justification='left', size=(10, 1), pad=(1,1), border_width=0,),
        sg.Text("", size=(6, 1)),
    ], [sg.HorizontalSeparator()]])

    column_layout = []
    balance = 0.0
    for row, (trans, ver) in enumerate(get_transactions_for_account(account)):
        balance += (trans.debit - trans.credit) * (-1 if account.is_debt or account.is_income else 1)
        color = alternative_background_color() if row % 2 else sg.theme_background_color()
        column_layout += [[sg.Column([[
            sg.Text("", size=(4, 1), background_color=color),
            sg.Text(ver.id, justification='left', size=(15, 1), pad=(1,1), border_width=0, background_color=color),
            sg.Text(str(ver.date), justification='left', size=(15, 1), pad=(1,1), border_width=0, background_color=color),
            sg.Text(trans.debit, justification='right', size=COLS["deb"].size[0], pad=(3,1), border_width=0, background_color=color),
            sg.Text(trans.credit, justification='right', size=COLS["cre"].size[0], pad=(3,1), border_width=0, background_color=color),
            sg.Text(balance, justification='right', size=(10, 1), pad=(1,1), border_width=0, background_color=color),
            sg.Text("", size=(6, 1), background_color=color),
        ]], background_color=color)]]

    return [header], [sg.Column(column_layout, scrollable=True, vertical_scroll_only=True, size=(None, 400), key="trans_acc_col")]


ROW_REGEX = re.compile(r'row(?P<row>\d+)_\w+')


def create_verifications_window() -> sg.Window:
    sg.set_options(element_padding=(0, 0))

    layout = [
        [
            sg.Text('Verifications', font='Any 18'),
            sg.Button('Prev', key='prev', pad=((10, 4), (2, 2))),
            sg.Button('Next', key='next', pad=(4, 2)),
            sg.VerticalSeparator(),
            sg.Button('New verification', key='new_ver', pad=(4, 2))
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Verification:"), sg.Text("?", key="ver_id")],
        [sg.Text("Date:"), sg.Text("?", key="ver_date"), sg.Button("Change date", key="ver_date_sel", pad=(10, 0))],
        [sg.Text("", key="discard_indicator", text_color="red", font="bold")],
        [sg.HorizontalSeparator()],
        [
            sg.Button('Validate and save verification', key="validate", pad=((0, 4), (4, 4))),
            sg.Button('Discard verification', key="discard_ver", pad=((4, 4), (4, 4))),
            sg.Button('Quit', pad=((4, 4), (4, 4)))
        ],
        [sg.Button("Add row", key="add_row", pad=(0, 1))],
        get_column_layout(),
        [sg.HorizontalSeparator()],
        [sg.Column(get_accumulation_layout(), key="accumulation_col")],
    ]

    return sg.Window('ALOPcounting Verifications', layout, size=(1000, 500), finalize=True, resizable=True)


def create_accounts_window() -> sg.Window:
    sg.set_options(element_padding=(0, 0))

    layout = [
        [
            sg.Text('Accounts', font='Any 18'),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button('New account', key="new_acc", pad=((0, 4), (4, 4))),
            sg.Button('Quit', pad=((4, 4), (4, 4)))
        ],
        get_accounts_column_layout(),
    ]

    return sg.Window('ALOPcounting Accounts', layout, size=(1000, 500), finalize=True, resizable=True)


def create_account_transactions_window(account: Account) -> sg.Window:
    sg.set_options(element_padding=(0, 0))

    layout = [
        [
            sg.Text(f'Transactions for account: {account.account_number}', font='Any 18'),
        ],
        [sg.HorizontalSeparator()],
        [sg.Text(account.description)],
        [sg.Button('Quit', pad=((0, 4), (4, 4)))],
        get_account_transactions_column_layout(account),
    ]

    return sg.Window('ALOPcounting Transactions for Account', layout, size=(600, 500), finalize=True, resizable=True)


def create_main_window() -> sg.Window:
    layout = [
        [sg.Text('ALOPcounting', font="Any 18")],
        [sg.Text('A simple open-source accounting programs, useful for smaller organizations.', font="Any 11 italic")],
        [sg.HorizontalSeparator()],
        [sg.Text("Year:"), sg.Text("?", key="current_year")],
        [
            sg.Button('Prev', key='prev_year', pad=((10, 4), (2, 2))),
            sg.Button('Next', key='next_year', pad=(4, 2)),
            sg.VerticalSeparator(),
            sg.Button('New year', key='new_year', pad=(4, 2))
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Number of verifications:"), sg.Text(account_list().len, key="num_verifications")],
        [sg.Text("Number of accounts:"), sg.Text(year().verification_list.len, key="num_accounts")],
        [sg.Button('Show accounts', size=(15, None))],
        [sg.Button('Show verifications', size=(15, None))],
        [sg.Text('')],
        [sg.Push(), sg.Button('Quit', size=(10, None))],
    ]

    # Create the Window
    return sg.Window('ALOPcounting Main', layout, finalize=True, resizable=True)


def main_loop():
    main_window = create_main_window()
    accounts_window = None
    verifications_window = None
    account_transactions_window = None

    current_ver_idx = 0
    ver_num_rows = 0
    repopulate_ver = True

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        # Update values
        main_window["num_accounts"].update(account_list().len)
        main_window["num_verifications"].update(year().verification_list.len)
        main_window["current_year"].update(year().year)
        if year().verification_list.len:
            ver = year().verification_list.get_verification_at(current_ver_idx)
        else:
            ver = Verification(0) # Fake verification

        if verifications_window is not None:
            if repopulate_ver and year().verification_list.len:
                populate_verification_layout(verifications_window, current_ver_idx)
                ver_num_rows = len(ver.transactions)
            repopulate_ver = False

            if ver_num_rows >= MAX_ROWS:
                verifications_window['add_row'].update(disabled=True)
            else:
                verifications_window['add_row'].update(disabled=False)

            if ver.discarded:
                verifications_window["discard_indicator"].update("DISCARDED")
                verifications_window["discard_ver"].update("Un-discard verification")
            else:
                verifications_window["discard_indicator"].update("")
                verifications_window["discard_ver"].update("Discard verification")

        # Read the event
        window, event, values = sg.read_all_windows()
        if window is None:
            sg.popup_error("read_all_windwos returned window == None ??!?")
            break

        # Main window
        if window == main_window:
            print("main_window", event)
            if event == sg.WIN_CLOSED or event == 'Quit':
                # Close all windows
                if accounts_window is None and verifications_window is None:
                    main_window.close()
                    break
                sg.popup("Close accounts and verifications windows first!")
            elif event == 'Show verifications' and verifications_window is None:
                verifications_window = create_verifications_window()
            elif event == 'Show accounts' and accounts_window is None:
                accounts_window = create_accounts_window()
            elif event == "prev_year":
                if accounts_window is None and verifications_window is None:
                    year().goto_prev_year()
                else:
                    sg.popup("Close accounts and verifications windows first!")
            elif event == "next_year":
                if accounts_window is None and verifications_window is None:
                    year().goto_next_year()
                else:
                    sg.popup("Close accounts and verifications windows first!")
            elif event == "new_year":
                if accounts_window is None and verifications_window is None:
                    year().create_new_year()
                    year().verification_list.save_verifications()
                else:
                    sg.popup("Close accounts and verifications windows first!")

        # Accounts window
        elif window == accounts_window:
            print("accounts_window", event)
            if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
                accounts_window.close()
                accounts_window = None

            elif event == 'new_acc':
                new_acc_num_input = sg.popup_get_text("Add new account number")
                if new_acc_num_input is None:
                    continue
                try:
                    new_acc_num = int(new_acc_num_input)
                except ValueError:
                    sg.popup(f"Bad account, '{new_acc_num_input}' not a number!")
                    continue
                if new_acc_num < 1000 or new_acc_num > 9999:
                    sg.popup(f"Bad account, '{new_acc_num}' outside accepted range (1000 - 9999)!")
                    continue
                if account_list().find_account(new_acc_num):
                    sg.popup(f"Bad account, '{new_acc_num}' already exists!")
                    continue
                new_acc_desc = sg.popup_get_text("Add new account description")
                new_acc = Account(new_acc_num, new_acc_desc)
                account_list().add_account(new_acc)
                account_list().save_accounts()
                # Reopen window to repopulate
                accounts_window.close()
                accounts_window = create_accounts_window()

            elif "_delete_acc" in event:
                match = ROW_REGEX.match(event)
                assert match, f"Bad event '{event}'"
                idx = int(match.group('row'))
                acc = account_list().get_accounts()[idx]
                ok = sg.popup_ok_cancel(f"Remove account {acc.account_number}?")
                if ok == "OK":
                    account_list().remove_account(acc)
                    account_list().save_accounts()
                    # Reopen window to repopulate
                    accounts_window.close()
                    accounts_window = create_accounts_window()

            elif "_acc_show_transactions" in event:
                match = ROW_REGEX.match(event)
                assert match, f"Bad event '{event}'"
                idx = int(match.group('row'))
                acc = account_list().get_accounts()[idx]
                if account_transactions_window is not None:
                    # Close and reopen with new account
                    account_transactions_window.close()
                account_transactions_window = create_account_transactions_window(acc)


        # Verifications window
        elif window == verifications_window:
            print("verifications_window", event)
            if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
                ok = "OK"
                if not cmp_verification_and_layout(ver, values):
                    ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes and quit?")
                if ok == "OK":
                    year().verification_list.save_verifications()
                    verifications_window.close()
                    verifications_window = None
                    current_ver_idx = 0
                    ver_num_rows = 0
                    repopulate_ver = True

            elif event == 'next':
                ok = "OK"
                if not cmp_verification_and_layout(ver, values):
                    ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
                if ok == "OK":
                    current_ver_idx += 1
                    repopulate_ver = True

            elif event == 'prev':
                ok = "OK"
                if not cmp_verification_and_layout(ver, values):
                    ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
                if ok == "OK":
                    current_ver_idx -= 1
                    repopulate_ver = True

            elif event == 'validate':
                if store_verification_from_layout(ver, values):
                    repopulate_ver = True

            elif event == "discard_ver":
                if store_verification_from_layout(ver, values):
                    ver.discarded = not ver.discarded
                    repopulate_ver = True

            elif "_delete" in event:
                match = ROW_REGEX.match(event)
                assert match, f"Bad event '{event}'"
                [verifications_window[f"row{match.group('row')}_{col}"].update('') for col in COLS.keys()]

            elif event == "add_row":
                ver_num_rows += 1
                verifications_window[f"row{ver_num_rows - 1}_idx"].update(visible=True)
                [verifications_window[f"row{ver_num_rows - 1}_{col}"].update(visible=True) for col in COLS.keys()]
                verifications_window[f"row{ver_num_rows - 1}_delete"].update(visible=True)

            elif event == "new_ver":
                ok = "OK"
                if not cmp_verification_and_layout(ver, values):
                    ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
                if ok == "OK":
                    current_ver_idx = year().verification_list.len
                    if date.today().year == year().year:
                        ver = Verification(id=current_ver_idx, date=date.today())
                    elif ver.date.year == year().year:
                        ver = Verification(id=current_ver_idx, date=ver.date)
                    else:
                        ver = Verification(id=current_ver_idx, date=date(year=year().year, month=1, day=1))
                    year().verification_list.add_verification(ver)
                    repopulate_ver = True

            elif event == "ver_date_sel":
                new_month, new_day, new_year = sg.popup_get_date(close_when_chosen=True, begin_at_sunday_plus=1, start_year=ver.date.year, start_mon=ver.date.month, start_day=ver.date.day)
                new_date = date(year=new_year, month=new_month, day=new_day)
                print("Date selected:", new_date)
                if new_date.year != year().year:
                    sg.popup(f"Chosen date not in current year! new_date.year {new_date.year}, year().year {year().year}")
                    continue
                ver.date = new_date
                verifications_window["ver_date"].update(ver.date)

        # Transactions for account window
        elif window == account_transactions_window:
            print("account_transactions_window", event)
            if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
                account_transactions_window.close()
                account_transactions_window = None


def create_html(filename: str):
    doc = dominate.document(title='ALOP Counting')

    with doc.head:
        # dt.link(rel='stylesheet', href='style.css')
        # dt.script(type='text/javascript', src='script.js')
        pass

    with doc:
        with dt.div(id='header'):
            pass

        with dt.div(style='margin: 50px'):
            dt.attr(cls='body')
            dt.h1('Accounts')
            with dt.table(style='text-align: left'):
                with dt.tr():
                    dt.th("Account", style="min-width: 100px")
                    dt.th("Description", style="min-width: 100px")
                for acc in account_list():
                    with dt.tr():
                        dt.td(acc.account_number)
                        dt.td(acc.description)

    with open(filename, "w") as html_file:
        html_file.write(str(doc))


def main():
    print(f"Running ALOPCounting, version: {__version__}")

    sg.theme('DarkAmber')

    if not config_init():
        sg.popup_error("Failed to load or create config!\n\nCheck logs for more info.")
        return
    account_list_init()
    verification_list_init()
    year_init()

    main_loop()

    config_do_git_commit("EXIT - Commit accounts and verifications")

    # create_html("content.html")
    # webbrowser.open_new_tab("content.html")

if __name__ == "__main__":
    main()
