# alopcounting
A.L-O.P. Simple Accounting Program

This is a small, basic program for accounting. This was created by me, [Andreas Pettersson](https://github.com/petterssonandreas), when virtually all accounting tools started to charge for the service. A basic program that was free was nowhere to be found, so I had to create one myself.

The intention of this program is not to replace Visma, Fortnox or similar, but to be a free to use tool for small organisations that cannot justify the ~300 SEK/month cost of a paid program. This program is NOT built for efficiency nor stability, but to be easy and fast to develop. With a lot of accounts and verifications, the program will be unusably slow. But, for the small organisation, it will be just enough.

⚠️ ***Remember to always backup your accounting!*** 

🔹 This program does use a local git to handle the accounting, but there is no server backup unless you do it yourself. And I make no promises that the usage of the program itself cannot lead to the deletion of the data.

# Usage
Download a release, unpack and run the executable: [Releases](https://github.com/petterssonandreas/alopcounting/releases)

Or, download the source code, install the Python requirements/dependencies, and run:

```
pip install -r requirements.txt
python main.py
```

# Work in progress / Still to do
A selection of things done and still to do:

### Reports
My thought here is to create simple html, and open in a browser. The user can then print a pdf.
- [ ] Create reports, eg. "resultatrapport" and "balansrapport"
- [ ] Custom time period for reports (year, or shorter)

### Invoices
- [ ] Incoming
  - Store info on payment, be able to mark it as paid later?
  - Be able to upload a pdf and store it?
- [ ] Outgoing
  - Create html/pdf
  - Logo? Info?

### Balance, transactions
- [x] View current balance for each account
- [x] View all transactions for an account
- [ ] Go to transaction
- [ ] Create printable report of all transactions for an account

### Cost units
- [ ] Add cost units ("resultatenhet")
- [ ] Create reports for a cost unit

### Customer register
- [ ] Add customer register
- [ ] Map invoices to customers

### Split years
- [x] incoming balance on accounts
- [ ] Compute incoming balance from previous year

### And probably much more...
