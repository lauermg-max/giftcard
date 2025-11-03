import importlib

import pytest


@pytest.fixture()
def service(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from giftcard_manager import config

    config.get_settings.cache_clear()

    database = importlib.reload(importlib.import_module("giftcard_manager.database"))
    importlib.reload(importlib.import_module("giftcard_manager.models"))
    importlib.reload(importlib.import_module("giftcard_manager.crud"))
    services = importlib.reload(importlib.import_module("giftcard_manager.services"))

    database.init_db()

    return services.GiftCardService()
