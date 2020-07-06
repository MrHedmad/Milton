import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from pathlib import Path
import os

from milton.config import CONFIG

# Setup logging
log = logging.getLogger("milton")  # Keep this at the module level name
log.setLevel(logging.DEBUG)
log.propagate = False
# Keep this at DEBUG - set levels in handlers themselves

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_LOG_PATH = CONFIG.logs.path

if Path(_LOG_PATH).parent.exists() is False:
    os.makedirs(Path(_LOG_PATH).parent)

file_h = RotatingFileHandler(
    filename=Path(_LOG_PATH), encoding="utf-8", mode="a+", maxBytes=1e5, backupCount=5,
)
file_h.setFormatter(formatter)
file_h.setLevel(CONFIG.logs.file_level)
stream_h = StreamHandler()
stream_h.setFormatter(formatter)
stream_h.setLevel(CONFIG.logs.stdout_level)

log.addHandler(file_h)
log.addHandler(stream_h)
