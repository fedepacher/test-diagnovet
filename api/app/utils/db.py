import logging
from peewee import SqliteDatabase
from peewee_async import PooledMySQLDatabase as PooledMySQLDatabaseAsync

from api.app.utils.settings import Settings


DB_NAME = Settings.db_name()
DB_USER = Settings.db_user()
DB_PASS = Settings.db_pass
DB_HOST = Settings.db_host
DB_PORT = Settings.db_port
DEPLOYMENT_SERVICE = Settings.deployment_service

if 'local' in DEPLOYMENT_SERVICE:
    logging.info(f"Connecting pool to local database at {DB_HOST}")
    db = PooledMySQLDatabaseAsync(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=int(DB_PORT)
    )
elif DEPLOYMENT_SERVICE == "cloud":
    logging.info("Using SQLite for cloud deployment")

    db = SqliteDatabase(
        "app.db",  # archivo local persistente
        pragmas={
            "journal_mode": "wal",
            "cache_size": -1024 * 64,
            "foreign_keys": 1,
        }
    )

else:
    raise ValueError(f"Unknown DEPLOYMENT_SERVICE: {DEPLOYMENT_SERVICE}")
