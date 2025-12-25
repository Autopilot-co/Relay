"""
Relay - Logging Configuration
Sets up logging to console and file with pretty formatting
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# -----------------------------------------------------------------------------
# STEP 1: Create a logs directory to store log files
# -----------------------------------------------------------------------------
# Path.cwd() = Current Working Directory (where the program runs from)
# / "logs" = Add "logs" folder to that path
# .mkdir() = Create the directory
# parents=True = Create parent folders if needed
# exist_ok=True = Don't error if it already exists
LOGS_DIR = Path.cwd() / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# STEP 2: Define how log messages should look (the format)
# -----------------------------------------------------------------------------
# This is like a template for every log message
# Example output: [2025-12-25 10:30:15] INFO: Server started
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"

# How timestamps should look
# %Y = Year (2025), %m = Month (12), %d = Day (25)
# %H = Hour (10), %M = Minute (30), %S = Second (15)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# -----------------------------------------------------------------------------
# STEP 3: Create the actual logger object
# -----------------------------------------------------------------------------
# Think of this as getting a notebook to write in
# "relay" is the name of this logger (we can have multiple loggers)
logger = logging.getLogger("relay")

# Set the minimum level - anything DEBUG and above gets logged
# DEBUG < INFO < WARNING < ERROR < CRITICAL
logger.setLevel(logging.DEBUG)


# -----------------------------------------------------------------------------
# STEP 4: Create a CONSOLE handler (prints to terminal)
# -----------------------------------------------------------------------------
# sys.stdout = Standard Output = Your terminal screen
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Only show INFO and above in terminal

# Create a formatter using our format template
console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
console_handler.setFormatter(console_formatter)


# -----------------------------------------------------------------------------
# STEP 5: Create a FILE handler (saves to a file)
# -----------------------------------------------------------------------------
# Create a filename with today's date: relay_2025-12-25.log
log_filename = f"relay_{datetime.now().strftime('%Y-%m-%d')}.log"
log_filepath = LOGS_DIR / log_filename

# FileHandler = Writes logs to a file
file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)  # Save EVERYTHING to file (including DEBUG)

# Use the same format for file logs
file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
file_handler.setFormatter(file_formatter)


# -----------------------------------------------------------------------------
# STEP 6: Attach both handlers to the logger
# -----------------------------------------------------------------------------
# Think of handlers like "destinations" for log messages
# Now when we log something, it goes to BOTH console AND file
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# -----------------------------------------------------------------------------
# STEP 7: Prevent duplicate logs (optional but important)
# -----------------------------------------------------------------------------
# This prevents logs from appearing multiple times
logger.propagate = False


# -----------------------------------------------------------------------------
# HOW TO USE THIS LOGGER:
# -----------------------------------------------------------------------------
# from utils.logger import logger
# 
# logger.debug("Detailed debugging info")
# logger.info("Something normal happened")
# logger.warning("Something unexpected but not broken")
# logger.error("Something broke!")
# logger.critical("Everything is on fire!")
# -----------------------------------------------------------------------------

