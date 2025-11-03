## Gift Card Manager

A desktop application for issuing and tracking gift cards sold for the merchants you support (Amazon, Best Buy, Lowe's, Walmart, and Home Depot). The app stores balances in a local SQLite database and ships with a GUI so you can quickly look up cards, add value, redeem purchases, and review the transaction history.

### Features
- Issue cards with custom codes, expiration dates, and notes
- Reload, redeem, or manually adjust balances with audit history
- Toggle cards active/inactive to prevent unauthorized use
- Filter cards by merchant or status and view transaction history at a glance
- Stores data in a per-user folder so multiple machines stay isolated

### Getting Started
1. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Launch the application**
   ```bash
   python main.py
   ```
   The database is created automatically on first launch in the OS-specific application data directory (see `giftcard_manager/config.py`).

### Build a Windows `.exe`
PyInstaller is included in `requirements.txt` so you can bundle the app after installing dependencies.

```bash
pyinstaller --noconfirm --noconsole --name GiftCardManager main.py
```

The packaged executable will be placed in the `dist/GiftCardManager` folder. Copy that folder to your PC and launch `GiftCardManager.exe` whenever you need the tool.

### Testing
Run the automated tests before distributing a new build:

```bash
pytest
```

### Project Layout
```
giftcard-manager/
├── giftcard_manager/
│   ├── __init__.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── enums.py
│   ├── exceptions.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── dialogs.py
│   │   ├── main_window.py
│   │   └── utils.py
│   ├── models.py
│   ├── schemas.py
│   └── services.py
├── tests/
│   └── __init__.py
├── main.py
├── requirements.txt
└── README.md
```

### Next Steps
- Add CSV export and import for bulk card management
- Create scheduled backups of the SQLite database
- Ship preset reporting for monthly sales and redemption totals
