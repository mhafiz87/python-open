# ruff: noqa: F401

import logging
import re
from datetime import datetime
from pathlib import Path


class StreamFormatter(logging.Formatter):
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\x1b[36m",  # Cyan
        logging.INFO: "\x1b[32m",  # Green
        logging.WARNING: "\x1b[33m",  # Yellow
        logging.ERROR: "\x1b[31m",  # Red
        logging.CRITICAL: "\x1b[41m",  # Red background
    }
    BOLD = "\x1b[1m"
    UNDERLINE = "\x1b[4m"
    RESET = "\x1b[0m"

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{self.BOLD}{color}{record.levelname}{self.RESET}"
        return super().format(record)


class FileFormatter(logging.Formatter):
    ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        formatted = super().format(record)
        return self.ANSI_PATTERN.sub("", formatted)


class CustomFileHandler(logging.FileHandler):
    def __init__(self, *args, separator_char="=", separator_length=80, **kwargs):
        super().__init__(*args, **kwargs)
        self.separator_line = "\n" + separator_char * separator_length + "\n\n"

    def write_separator(self):
        """Write a raw separator line without formatting"""
        if self.stream:
            self.stream.write(self.separator_line)
            self.stream.flush()

    def write_header(self, title):
        """Write a formatted header block"""
        if self.stream:
            self.stream.write(self.separator_line)
            self.stream.write(f"{title}\n")
            self.stream.write(self.separator_line)
            self.stream.flush()


log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.DEBUG)
log_stream_handler.setFormatter(
    StreamFormatter(
        fmt="%(asctime)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s",
        # datefmt="%Y%m%d_%H:%M:%S",
    )
)

log_file_handler = CustomFileHandler(
    filename=f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}_dtsx.log",
    mode="a",
    encoding="utf-8",
)
log_file_handler.setLevel(logging.DEBUG)
log_file_handler.setFormatter(
    FileFormatter(
        fmt="%(asctime)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s",
        # datefmt="%Y%m%d_%H%M%S",
    )
)

logger.addHandler(log_stream_handler)
logger.addHandler(log_file_handler)
