from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.app.utils.db import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application’s lifecycle, ensuring that the database connection
    is opened and remains active during the application’s runtime.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Indicates the context of the application's lifespan.
    """
    if db.is_closed():
        db.connect(reuse_if_open=True)

    try:
        yield
    finally:
        if not db.is_closed():
            db.close()