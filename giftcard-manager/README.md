## Gift Card Manager

This project provides a lightweight REST API for managing gift cards, balances, and transaction history for a small business. It is built with FastAPI and SQLite so you can run it locally without additional infrastructure.

### Features
- Issue new gift cards with optional custom codes and expiration dates
- Track balances, reloads, and redemptions with transaction history
- Prevent redemptions on inactive or expired cards and enforce balance checks
- Simple JSON API ready to connect to point-of-sale systems or admin dashboards

### Getting Started
1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run database migrations**
   The app auto-creates tables on first run using SQLAlchemy metadata.
3. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```
4. **Explore the API**
   Visit `http://127.0.0.1:8000/docs` for interactive Swagger docs.

### Running Tests
```bash
pytest
```

### Environment Variables
- `DATABASE_URL` (optional): Override the default SQLite database path.

### Project Structure
```
giftcard-manager/
├── app/
│   ├── __init__.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   └── giftcards.py
│   └── schemas.py
├── tests/
│   ├── __init__.py
│   └── test_giftcards.py
├── requirements.txt
└── README.md
```

### Next Steps
- Add authentication and role-based access control
- Create a lightweight admin dashboard
- Integrate email notifications for gift card issuance and low balances
