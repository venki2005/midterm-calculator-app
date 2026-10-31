"""Application logging setup."""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Determine log file and encoding with safe fallbacks
LOG_DIR = Path(os.getenv("CALCULATOR_LOG_DIR", "logs"))
LOG_FILE = Path(os.getenv("CALCULATOR_LOG_FILE", "logs/calculator.log"))
DEFAULT_ENCODING = os.getenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")

# Ensure the log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger("EnhancedCalculator")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    )

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_ENCODING)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console / Terminal Stream Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)