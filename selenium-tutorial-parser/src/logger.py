# ruff: noqa: F401

import logging
import re


class StreamFormatter(logging.Formatter):
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{self.BOLD}{color}{record.levelname}{self.RESET}"
        return super().format(record)


class FileFormatter(logging.Formatter):
    _ansi_escape_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\\[0-?]*[ -/]*[@-~])")

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        # Remove the escape codes from the formatted message
        formatted_message = super().format(record)
        return self._ansi_escape_regex.sub("", formatted_message)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.DEBUG)
log_stream_handler.setFormatter(
    StreamFormatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")
)

log_file_handler = logging.FileHandler("dtsx.log")
log_file_handler.setLevel(logging.DEBUG)
log_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")
)

# logger.addHandler(log_file_handler)
logger.addHandler(log_stream_handler)
