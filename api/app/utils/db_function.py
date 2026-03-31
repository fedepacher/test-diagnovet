import logging
from api.app.utils.create_tables import create_tables
from api.app.utils.fill_tables import fill_all_tables


def handler_db():
    """Create tables and fill them."""
    logging.info("Handling database tables")
    create_tables()
    fill_all_tables()
