import logging
import os
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

from colorama import Back, Fore, Style
from prompt_toolkit.patch_stdout import StdoutProxy

from milton.core.config import CONFIG

__all__ = ["__version__", "CHANGELOG"]

__version__ = "1.1.0"

# Setup logging
log = logging.getLogger("milton")  # Keep this at the module level name
log.setLevel(logging.DEBUG)
log.propagate = False
# Keep this at DEBUG - set levels in handlers themselves

log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class ColorFormatter(logging.Formatter):
    # Change this dictionary to suit your coloring needs!
    COLORS = {
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Style.BRIGHT + Fore.MAGENTA,
        "INFO": Fore.GREEN,
        "CRITICAL": Style.BRIGHT + Fore.RED,
    }

    def format(self, record):
        reset = Fore.RESET + Back.RESET + Style.NORMAL
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.name = Style.BRIGHT + Fore.CYAN + record.name + reset
            if record.levelname != "INFO":
                record.msg = color + str(record.msg) + reset
            record.levelname = color + record.levelname + reset
        return logging.Formatter.format(self, record)


console_formatter = ColorFormatter(log_format)
file_formatter = logging.Formatter(log_format)

_LOG_PATH = Path(CONFIG.logs.path).expanduser().resolve()

if _LOG_PATH.parent.exists() is False:
    os.makedirs(Path(_LOG_PATH).parent)

file_h = RotatingFileHandler(
    filename=Path(_LOG_PATH),
    encoding="utf-8",
    mode="a+",
    maxBytes=1e5,
    backupCount=5,
)
file_h.setFormatter(file_formatter)
file_h.setLevel(CONFIG.logs.file_level)
stream_h = StreamHandler(StdoutProxy(raw=True))
stream_h.setFormatter(console_formatter)
stream_h.setLevel(CONFIG.logs.stdout_level)

log.addHandler(file_h)
log.addHandler(stream_h)
