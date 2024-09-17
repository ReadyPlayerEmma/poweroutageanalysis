"""The core module of the poweroutageanalysis package."""

import logging
import time

from dotenv import load_dotenv

load_dotenv()

ORIGINAL_DATA_PATH = "data/original/"


def main() -> None:
    """Initialize the PowerOutageAnalysis class."""
    PowerOutageAnalysis()


class PowerOutageAnalysis:
    """Main class to analyze power outages."""

    log: logging.Logger

    def __init__(self) -> None:
        """Initialize PowerOutageAnalysis class."""
        logging.basicConfig(level=logging.INFO)

        # Set the default logger settings

        # Default log level is INFO
        logging.basicConfig(level=logging.INFO)

        # Let's make sure the log level names have colors
        logging.addLevelName(logging.INFO, f"\033[1;34m{logging.getLevelName(logging.INFO)}\033[1;0m")
        logging.addLevelName(logging.WARNING, f"\033[1;33m{logging.getLevelName(logging.WARNING)}\033[1;0m")
        logging.addLevelName(logging.ERROR, f"\033[1;31m{logging.getLevelName(logging.ERROR)}\033[1;0m")
        logging.addLevelName(logging.CRITICAL, f"\033[1;41m{logging.getLevelName(logging.CRITICAL)}\033[1;0m")

        # Let's make sure the logs have a nice format
        log_format = "\033[1;30m%(asctime)s\033[1;0m %(levelname)s \033[35m%(name)s\033[0m %(message)s"

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        formatter.converter = time.gmtime  # Use UTC time

        # Create a logger for this module
        self.log = logging.getLogger(__name__)

        # Set the format for all log handlers
        for handler in logging.getLogger().handlers:
            self.log.info(f"Setting formatter for handler {handler}")
            handler.setFormatter(formatter)

        self.log.info("Initializing PowerOutageAnalysis")

        self.analyze_power_outages()

    def analyze_power_outages(self) -> None:
        """Analyze power outages."""
        self.log.info("Analyzing power outages")

        self.load_data()

    def load_data(self) -> None:
        """Load data from the database."""
        self.log.info("Loading data from the filesystem")
