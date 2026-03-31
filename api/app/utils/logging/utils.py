"""
Utility functions for logging.
"""

import logging

from api.app.utils.settings import Settings


# Configure specific logging levels for external libraries
def configure_library_loggers(library_loggers: dict, handlers: list) -> None:
    """
    Configure logging levels for specific external libraries based on environment.

    Args:
        library_loggers (dict): A dictionary mapping library names to their logging levels.

    Returns:
        None
    """

    # Apply logging levels to each library
    for lib_name, level in library_loggers.items():
        logging.getLogger(lib_name).setLevel(level)
        # Ensure library logs use the same handlers as the root logger
        logging.getLogger(lib_name).handlers = handlers


def get_logging_level_by_env() -> int:
    """
    Get the logging level from the environment variable.

    Returns:
        int: The logging level for the current environment.
    """
    if Settings.run_env in ['prod', 'production']:
        log_level = logging.INFO
    elif Settings.run_env in ['beta']:
        log_level = logging.INFO
    elif Settings.run_env in ['dev', 'development', 'qa']:
        log_level = logging.DEBUG
    else:
        log_level = logging.NOTSET

    return log_level
