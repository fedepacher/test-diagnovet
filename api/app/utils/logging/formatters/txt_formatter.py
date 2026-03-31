"""Custom TXT formatter for Local Logging."""

from logging import Formatter

from colorama import Fore, Style
from datetime import datetime

# Códigos de colores ANSI
COLORS = {
	'DEBUG': Fore.BLUE,
	'INFO': Fore.GREEN,
	'WARN': Fore.YELLOW,
	'WARNING': Fore.YELLOW,
	'ERROR': Fore.RED,
	'FATAL': Fore.RED,
	'CRITICAL': Fore.MAGENTA,
	'RESET': Style.RESET_ALL
}

class TXTFormatter(Formatter):
	"""Custom TXT formatter for Local Logging."""
	def format(self, record):
		# Format timestamp
		timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

		# Assign color based on log level
		color = COLORS.get(record.levelname, COLORS['RESET'])
		reset = COLORS['RESET']

		return(
			f"{color}"
			f"{timestamp}"
			f" - (PID:{record.process})"    # Workers
			f" - {record.levelname}"
			f" - [{record.name} ~ {record.filename}:{record.lineno}]"
			f": {record.getMessage()}"
			f"{reset}"
		)