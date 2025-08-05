# hero_service/settings_test.py
from .settings import *  # noqa

# Тестовая БД — SQLite, чтобы pytest не зависел от Postgres/сети Docker
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",
        # ВАЖНО: Django 5.2 ожидает наличие этого ключа, иначе KeyError в тестовом клиенте
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        # Опционально:
        # "TEST": {"NAME": BASE_DIR / "test.sqlite3"},
    }
}
