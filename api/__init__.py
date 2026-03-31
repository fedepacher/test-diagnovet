"""
Module initializer for logging configuration.

This module sets up the logging configuration for the application,
allowing logs to be written either to a file (if specified via
the `LOG_FILE` environment variable) or to the console.
"""

import logging

from logging.handlers import TimedRotatingFileHandler
from colorama import init

from api.app.utils.logging.formatters.txt_formatter import TXTFormatter
from api.app.utils.logging.utils import configure_library_loggers, get_logging_level_by_env
from api.app.utils.settings import Settings

# Start Colorama for cross-platform compatibility
init(autoreset=True)

# Configure logging to output to the console
console_handler = logging.StreamHandler()

# Set the formatter for the console handler
console_handler.setFormatter(TXTFormatter())

# Create a list to hold all handlers
handlers = [console_handler]

# Configure logging to write to the specified file
if Settings.log_file:

	# file_handler = logging.FileHandler(Settings.log_file)
	# Configure the file handler for daily rotation
	file_handler = TimedRotatingFileHandler(
    Settings.log_file,
    when='midnight',   # Rotate at midnight
    interval=1,        # Every 1 day
    backupCount=30     # Keep logs for the last 30 days
	)

	file_handler.setFormatter(TXTFormatter())   # Always TXT for local files

	handlers.append(file_handler)

logging.basicConfig(
	level=get_logging_level_by_env(),
	handlers=handlers
)

library_loggers = {
	'asyncio': logging.WARNING,
	'peewee': logging.INFO,
	'urllib3': logging.WARNING,
}

# Call the function to configure library-specific loggers
configure_library_loggers(library_loggers, handlers)
