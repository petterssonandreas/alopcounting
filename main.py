
import re
from typing import Any
from account import Account, load_accounts, find_account
from transaction import Transaction
from verification import Verification, load_verifications, save_verifications
import PySimpleGUI as sg
import pprint
import dataclasses as dc



@dc.dataclass
class ColInfo:
    name: str
    size: tuple[int, int]


COLS = {
    "acc": ColInfo("Account", (10, 1)),
    "des": ColInfo("Description", (30, 1)),
    "cre": ColInfo("Kredit", (10, 1)),
    "deb": ColInfo("Debet", (10, 1)),
    "not": ColInfo("Notes", (50, 1)),
}
MAX_ROWS = 20
MAX_COL = 5


def populate_verification_layout(verifications: list[Verification], window: sg.Window, current_ver_idx: int):
    ver = verifications[current_ver_idx]
    window["ver_id"].update(ver.id)
    window["ver_date"].update(ver.date)

    if current_ver_idx == 0:
        window['prev'].update(disabled=True)
    else:
        window['prev'].update(disabled=False)
    if current_ver_idx == (len(verifications) - 1):
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
        window[f"row{i}_cre"].update(trans.credit)
        window[f"row{i}_deb"].update(trans.debit)
        window[f"row{i}_not"].update(trans.notes)


def store_verification_from_layout(verification: Verification, values: dict[str: str], accounts: list[Account]):
    rows_dict = {row: {k: v for k, v in values.items() if f"row{row}_" in k} for row in range(MAX_ROWS)}
    new_transes = []
    for row, vals in rows_dict.items():
        if not vals[f"row{row}_acc"]:
            continue

        acc_val = vals[f"row{row}_acc"]
        acc = find_account(acc_val, accounts)
        if not acc:
            sg.popup(f"Row {row}: No account with number '{acc_val}'!")
            return

        new_transes.append(Transaction(acc, vals[f"row{row}_cre"], vals[f"row{row}_deb"], vals[f"row{row}_not"]))

    verification.transactions = new_transes
    pprint.pprint(new_transes, indent=4)

def get_column_layout() -> list[list[Any]]:
    columm_layout = [
        [sg.Text("", size=(4, 1))] +
        [sg.Text(COLS["acc"].name, justification='left', size=COLS["acc"].size, pad=(0,0), border_width=0)] +
        [sg.Text(COLS["des"].name, justification='left', size=COLS["des"].size, pad=(0,0), border_width=0)] +
        [sg.Text(COLS["cre"].name, justification='left', size=COLS["cre"].size, pad=(0,0), border_width=0)] +
        [sg.Text(COLS["deb"].name, justification='left', size=COLS["deb"].size, pad=(0,0), border_width=0)] +
        [sg.Text(COLS["not"].name, justification='left', size=COLS["not"].size, pad=(0,0), border_width=0)] +
        [sg.Text("", size=(4, 1))]
    ]
    columm_layout += [
        [sg.Text(str(row), size=(4, 1), justification='right', key=f"row{row}_idx")] +
        [sg.InputText(size=COLS["acc"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_acc")] +
        [sg.InputText(size=COLS["des"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_des")] +
        [sg.InputText(size=COLS["cre"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_cre")] +
        [sg.InputText(size=COLS["deb"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_deb")] +
        [sg.InputText(size=COLS["not"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_not")] +
        [sg.Button("X", key=f"row{row}_delete", pad=(3, 0))]
        for row in range(MAX_ROWS)
    ]
    return columm_layout

ROW_REGEX = re.compile(r'row(?P<row>\d+)_\w+')

def verifications_window_loop(accounts: list[Account], verifications: list[Verification]):

    sg.set_options(element_padding=(0, 0))

    layout = [
        [sg.Text('Verifications')],
        [sg.HorizontalSeparator()],
        [sg.Text("Verification"), sg.Text("?", key="ver_id")],
        [sg.Text("Date"), sg.Text("?", key="ver_date")],
        [sg.HorizontalSeparator()],
        [sg.Button('Prev', key='prev'), sg.Button('Next', key='next')],
        [sg.Button('Save verification'), sg.Button('Quit')],
        [sg.Column(get_column_layout(), size=(1000, 600), scrollable=True, key="ver_col")],
    ]

    current_ver_idx = 0

    # Create the Window
    window = sg.Window('ALOPcounting VERIFICATION', layout, finalize=True, resizable=True)
    # Event Loop to process "events" and get the "values" of the inputs
    repopulate = True
    while True:
        if repopulate:
            populate_verification_layout(verifications, window, current_ver_idx)
        repopulate = False

        event, values = window.read()
        print(event, values)

        if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
            break
        if event == 'next':
            current_ver_idx += 1
            repopulate = True
        if event == 'prev':
            current_ver_idx -= 1
            repopulate = True
        if event == 'Save verification':
            store_verification_from_layout(verifications[current_ver_idx], values, accounts)
            repopulate = True
        if "_delete" in event:
            match = ROW_REGEX.match(event)
            assert match, f"Bad event '{event}'"
            [window[f"row{match.group('row')}_{col}"].update('') for col in COLS.keys()]

    window.close()

def main_window_loop(accounts: list[Account], verifications: list[Verification]):
    # All the stuff inside your window.
    layout = [
        [sg.Text('ALOPcounting')],
        [sg.Text("Number of verifications:"), sg.Text("?", key="num_verifications")],
        [sg.Text("Number of accounts:"), sg.Text("?", key="num_accounts")],
        [sg.Button('Show accounts')],
        [sg.Button('Show verifications')],
        [sg.Button('Quit')],
    ]

    # Create the Window
    window = sg.Window('ALOPcounting MAIN', layout, finalize=True, resizable=True)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window["num_accounts"].update(len(accounts))
        window["num_verifications"].update(len(verifications))
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
            break
        if event == 'Show verifications':
            verifications_window_loop(accounts, verifications)

    window.close()


def main():
    sg.theme('DarkAmber')   # Add a touch of color

    # acc = Account(1920, "Plusgiro")
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

    main_window_loop(accounts, verifications)

    save_verifications("example_verifications", verifications)

if __name__ == "__main__":
    main()
