
import re
from typing import Any
from account import Account, account_list
from transaction import Transaction
from verification import Verification, verification_list
import PySimpleGUI as sg
import pprint
import dataclasses as dc
import dominate
import dominate.tags as dt
import webbrowser

@dc.dataclass
class ColInfo:
    name: str
    size: tuple[int, int]


COLS = {
    "acc": ColInfo("Account", (10, 1)),
    "des": ColInfo("Description", (30, 1)),
    "deb": ColInfo("Debet", (10, 1)),
    "cre": ColInfo("Kredit", (10, 1)),
    "not": ColInfo("Notes", (50, 1)),
}
MAX_ROWS = 20


def populate_verification_layout(window: sg.Window, current_ver_idx: int):
    ver = verification_list.get_verification_at(current_ver_idx)
    window["ver_id"].update(ver.id)
    window["ver_date"].update(ver.date)

    if current_ver_idx == 0:
        window['prev'].update(disabled=True)
    else:
        window['prev'].update(disabled=False)
    if current_ver_idx == (verification_list.len - 1):
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
        acc = account_list.find_account(acc_val)
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


def get_column_layout() -> list[list[Any]]:
    columm_layout = [
        [sg.Text("", size=(4, 1))] +
        [sg.Text(COLS["acc"].name, justification='left', size=COLS["acc"].size[0] + 1, pad=(1,1), border_width=0,)] +
        [sg.Text(COLS["des"].name, justification='left', size=COLS["des"].size[0], pad=(1,1), border_width=0,)] +
        [sg.Text(COLS["deb"].name, justification='left', size=COLS["deb"].size[0] - 2, pad=(1,1), border_width=0,)] +
        [sg.Text(COLS["cre"].name, justification='left', size=COLS["cre"].size[0] - 1, pad=(1,1), border_width=0,)] +
        [sg.Text(COLS["not"].name, justification='left', size=COLS["not"].size[0] - 4, pad=(1,1), border_width=0,)] +
        [sg.Text("", size=(3, 0))]
    ]
    columm_layout += [
        [sg.Text(str(row), size=(4, 1), justification='right', key=f"row{row}_idx")] +
        [sg.Combo(values=[acc.account_number for acc in account_list], size=COLS["acc"].size, pad=(1,1), key=f"row{row}_acc")] +
        [sg.Text(size=COLS["des"].size, pad=(1,1), border_width=0, justification='left', key=f"row{row}_des")] +
        [sg.InputText(size=COLS["deb"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_deb")] +
        [sg.InputText(size=COLS["cre"].size, pad=(1,1), border_width=0, justification='right', key=f"row{row}_cre")] +
        [sg.InputText(size=COLS["not"].size, pad=(1,1), border_width=0, justification='left', key=f"row{row}_not")] +
        [sg.Button("X", key=f"row{row}_delete", pad=(3, 0))]
        for row in range(MAX_ROWS)
    ]
    return columm_layout


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
    columm_layout = [
        [sg.Text("", size=(4, 1))] +
        [sg.Text("Account", justification='left', size=(6, 1), pad=(1,1), border_width=0,)] +
        [sg.Text("Description", justification='left', size=(80, 1), pad=(1,1), border_width=0,)] +
        [sg.Text("", size=(3, 0))],
    ]
    for row, acc in enumerate(account_list):
        columm_layout += [
            [sg.Text("", size=(4, 1))] +
            [sg.Text(acc.account_number, justification='left', size=(6, 1), pad=(1,1), border_width=0,)] +
            [sg.Text(acc.description, justification='left', size=(80, 1), pad=(1,1), border_width=0,)] +
            [sg.Button("X", key=f"row{row}_delete_acc", pad=(3, 0))],
        ]
    return columm_layout


ROW_REGEX = re.compile(r'row(?P<row>\d+)_\w+')


def verifications_window_loop():

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
        [sg.Text("Date:"), sg.Text("?", key="ver_date")],
        [sg.Text("", key="discard_indicator", text_color="red", font="bold")],
        [sg.HorizontalSeparator()],
        [
            sg.Button('Validate and save verification', key="validate", pad=((0, 4), (4, 4))),
            sg.Button('Discard verification', key="discard_ver", pad=((4, 4), (4, 4))),
            sg.Button('Quit', pad=((4, 4), (4, 4)))
        ],
        [sg.Button("Add row", key="add_row", pad=(0, 1))],
        [sg.Column(get_column_layout(), scrollable=True, vertical_scroll_only=True, size=(1000, 300), key="ver_col")],
        [sg.HorizontalSeparator()],
        [sg.Column(get_accumulation_layout(), key="accumulation_col")],
    ]

    current_ver_idx = 0
    num_rows = 0

    # Create the Window
    window = sg.Window('ALOPcounting VERIFICATION', layout, size=(1000, 500), finalize=True, resizable=True)
    # Event Loop to process "events" and get the "values" of the inputs
    repopulate = True
    while True:
        ver = verification_list.get_verification_at(current_ver_idx)

        if repopulate and verification_list.len:
            populate_verification_layout(window, current_ver_idx)
            num_rows = len(ver.transactions)
        repopulate = False

        if num_rows >= MAX_ROWS:
            window['add_row'].update(disabled=True)
        else:
            window['add_row'].update(disabled=False)

        if ver.discarded:
            window["discard_indicator"].update("DISCARDED")
            window["discard_ver"].update("Un-discard verification")
        else:
            window["discard_indicator"].update("")
            window["discard_ver"].update("Discard verification")

        event, values = window.read()
        print(event)

        if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
            ok = "OK"
            if not cmp_verification_and_layout(ver, values):
                ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes and quit?")
            if ok == "OK":
                verification_list.save_verifications()
                break

        if event == 'next':
            ok = "OK"
            if not cmp_verification_and_layout(ver, values):
                ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
            if ok == "OK":
                current_ver_idx += 1
                repopulate = True

        if event == 'prev':
            ok = "OK"
            if not cmp_verification_and_layout(ver, values):
                ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
            if ok == "OK":
                current_ver_idx -= 1
                repopulate = True

        if event == 'validate':
            if store_verification_from_layout(ver, values):
                repopulate = True

        if event == "discard_ver":
            if store_verification_from_layout(ver, values):
                ver.discarded = not ver.discarded
                repopulate = True

        if "_delete" in event:
            match = ROW_REGEX.match(event)
            assert match, f"Bad event '{event}'"
            [window[f"row{match.group('row')}_{col}"].update('') for col in COLS.keys()]

        if event == "add_row":
            num_rows += 1
            window[f"row{num_rows - 1}_idx"].update(visible=True)
            [window[f"row{num_rows - 1}_{col}"].update(visible=True) for col in COLS.keys()]
            window[f"row{num_rows - 1}_delete"].update(visible=True)

        if event == "new_ver":
            ok = "OK"
            if not cmp_verification_and_layout(ver, values):
                ok = sg.popup_ok_cancel("Verification has changed and not been saved, discard changes?")
            if ok == "OK":
                current_ver_idx = verification_list.len
                ver = Verification(id=current_ver_idx)
                verification_list.add_verification(ver)
                repopulate = True

    window.close()


def accounts_window_loop() -> bool:
    """
    Returns true if function should be called again
    This is because adding and deleting accounts need to redraw/repopulate
    """
    ret = False

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
        [sg.Column(get_accounts_column_layout(), scrollable=True, vertical_scroll_only=True, size=(800, 400), key="acc_col")],
    ]

    # Create the Window
    window = sg.Window('ALOPcounting ACCOUNTS', layout, size=(1000, 500), finalize=True, resizable=True)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        print(event)

        if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
            break

        if event == 'new_acc':
            new_acc_num_input = sg.popup_get_text("Add new account number")
            try:
                new_acc_num = int(new_acc_num_input)
            except ValueError:
                sg.popup(f"Bad account, '{new_acc_num_input}' not a number!")
                continue
            if new_acc_num <= 1000 or new_acc_num > 9999:
                sg.popup(f"Bad account, '{new_acc_num}' outside accepted range (1000 - 9999)!")
                continue
            if account_list.find_account(new_acc_num):
                sg.popup(f"Bad account, '{new_acc_num}' already exists!")
                continue
            new_acc_desc = sg.popup_get_text("Add new account description")
            new_acc = Account(new_acc_num, new_acc_desc)
            account_list.add_account(new_acc)
            account_list.save_accounts()
            ret = True
            break

        if "_delete_acc" in event:
            match = ROW_REGEX.match(event)
            assert match, f"Bad event '{event}'"
            idx = int(match.group('row'))
            acc = account_list.get_accounts()[idx]
            ok = sg.popup_ok_cancel(f"Remove account {acc.account_number}?")
            if ok == "OK":
                account_list.remove_account(acc)
                account_list.save_accounts()
                ret = True
                break

    window.close()
    return ret


def main_window_loop():
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
        window["num_accounts"].update(account_list.len)
        window["num_verifications"].update(verification_list.len)
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks quit
            break
        if event == 'Show verifications':
            verifications_window_loop()
        if event == 'Show accounts':
            while accounts_window_loop():
                pass

    window.close()


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
                for acc in account_list:
                    with dt.tr():
                        dt.td(acc.account_number)
                        dt.td(acc.description)

    with open(filename, "w") as html_file:
        html_file.write(str(doc))


def main():
    sg.theme('DarkAmber')

    main_window_loop()

    # create_html("content.html")
    # webbrowser.open_new_tab("content.html")

if __name__ == "__main__":
    main()
