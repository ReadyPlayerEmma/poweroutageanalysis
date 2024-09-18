"""The core module of the poweroutageanalysis package."""

from __future__ import annotations

import asyncio
import csv
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from poweroutageanalysis.ai import PowerOutageAI
from poweroutageanalysis.types import PowerOutageEvent
from poweroutageanalysis.util import clean_num_string

load_dotenv()

ORIGINAL_DATA_PATH = "data/original/"
FILE_SUFFIX = "_Annual_Summary"
FILE_SUFFIX_CSV = "_Annual_Summary_Converted"

NORMALIZED_DATA_PATH = "data/normalized/"
NORMALIZED_SUFFIX = "_Normalized"

# Set the range of years to process
YEAR_RANGE = range(2002, 2003)

# 2000 and 2001 have been parsed out of the PDFs into the CSV files (using ChatGPT).
# This is due to the fact that only the PDF was available for those years.
# All remaining years are in the Excel files.

# We will work with only the XLS files and the parsed CSV files.
# Even though they are all in columns and rows now, they don't have consistent column names or column ordering.

# The data itself is not consistent from year to year either.
# We will need to use OpenAI's models to parse the data into a consistent format.


def main() -> None:
    """Initialize the PowerOutageAnalysis class."""
    PowerOutageAnalysis()


class PowerOutageAnalysis:
    """Main class to analyze power outages."""

    log: logging.Logger
    data: list[PowerOutageEvent]
    ai: PowerOutageAI

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

        self.ai = PowerOutageAI()

        self.data = []
        self.analyze_power_outages()

    def analyze_power_outages(self) -> None:
        """Analyze power outages."""
        self.log.info("Analyzing power outages")

        self.load_data()

        asyncio.run(self.augment_data_with_ai())

        self.log.warning("DONE ANALYZING POWER OUTAGES")
        self.log.warning("OUTPUTTING RESULTS")
        asyncio.run(self.output_results())

    def load_data(self) -> None:
        """Load data from the database."""
        self.log.info("Loading data from the filesystem")

        # Get a list of all the files in the data/original directory
        files = os.listdir(ORIGINAL_DATA_PATH)
        self.log.info(f"Found {len(files)} files in the data/original directory")

        # Filter the list to only include XLS files
        xls_files = [file for file in files if file.endswith(".xls")]
        self.log.info(f"Found {len(xls_files)} XLS files in the data/original directory")

        # Filter the list to only include CSV files
        csv_files = [file for file in files if file.endswith(".csv")]
        self.log.info(f"Found {len(csv_files)} CSV files in the data/original directory")

        # Log year range
        self.log.info(f"Processing data for years {YEAR_RANGE}")

        for year in YEAR_RANGE:
            self.log.info(f"Processing data for {year}")
            if f"{year}{FILE_SUFFIX}.xls" in xls_files:
                self.process_xls_file(year)
            elif f"{year}{FILE_SUFFIX_CSV}.csv" in csv_files:
                self.process_csv_file(year)
            else:
                msg = f"No data file found for {year}"
                raise FileNotFoundError(msg)

    def process_csv_file(self, year: int) -> None:
        """Process a CSV file."""
        self.log.info(f"Processing CSV file for {year}")

        # Combine the path and filename
        file_path = Path(ORIGINAL_DATA_PATH) / f"{year}{FILE_SUFFIX_CSV}.csv"

        # Read the csv into memory
        rows = []
        self.log.info(f"Reading data from {file_path}")

        # Read in the CSV file
        with file_path.open("r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
            rows = list(reader)
        self.log.info(f"Found {len(rows)} rows in the CSV file")

        # Process the data
        for row in rows:
            self.log.info(row)
            customers_affected: int | None
            try:
                customers_affected = clean_num_string(row["Number of Customers Affected"])
            except ValueError:
                self.log.warning("customers_affected ValueError, trying to fix with AI")
                customers_affected = asyncio.run(self.ai.fix_number(row["Number of Customers Affected"]))

            demand_loss_mw: int | None
            try:
                demand_loss_mw = clean_num_string(row["Loss (megawatts)"])
            except ValueError:
                self.log.warning("demand_loss_mw ValueError, trying to fix with AI")
                demand_loss_mw = asyncio.run(self.ai.fix_number(row["Loss (megawatts)"]))

            # Try to parse out the region from the utility name.
            # Sometimes the region is in parentheses at the end of the utility name.
            # Region names are always 2 to 6 letters long in uppercase.

            region = None
            utility_name = row["Utility/Power Pool (NERC Council)"].strip()
            if utility_name and utility_name[-1] == ")":
                # Try to find the region in parentheses at the end of the utility name
                match = re.search(r"\(([A-Z]{2,6})\)$", utility_name)
                if match:
                    region = match.group(1)
                    utility_name = utility_name[: match.start()].strip()

            try:
                event = PowerOutageEvent(
                    date=row["Date"],
                    time=row["Time"],
                    region=region,
                    area_affected=row["Area"],
                    customers_affected=customers_affected,
                    demand_loss_mw=demand_loss_mw,
                    outage_type=row["Type of Disturbance"],
                    utility_name=utility_name,
                    restoration_time=row["Restoration Time"],
                )
                self.data.append(event)
                self.log.info(f"SUCCESSFULLY PROCESSED ROW:\n{event}")
            except KeyError:
                self.log.exception("Error processing row, column mismatch")
            except ValueError:
                self.log.exception("Error processing row, value error")

    def process_xls_file(self, year: int) -> None:
        """Process an XLS file.

        Args:
            year (int): The year of the XLS file to process.

        """
        self.log.info(f"Processing XLS file for {year}")

        # Combine the path and filename
        file_path = Path(ORIGINAL_DATA_PATH) / f"{year}{FILE_SUFFIX}.xls"

        # Read the XLS file into memory
        rows = []
        self.log.info(f"Reading data from {file_path}")

        xls_df = pd.read_excel(file_path)
        xls_df = pd.read_excel(file_path, header=None)

        # Find the row index of the header row
        header_row_index = xls_df.iloc[:, 2].first_valid_index()

        # Set the header row as the column names and skip rows above it
        xls_df.columns = xls_df.iloc[header_row_index]
        xls_df = xls_df[header_row_index + 1 :]

        rows = xls_df.to_dict(orient="records")

        self.log.info(f"Found {len(rows)} rows in the XLS file")

        # Process the data
        for row in rows:
            self.log.info(row)

            if "Date" in row and not isinstance(row["Date"], datetime):
                # Skip rows that don't have a valid date
                self.log.warning("Skipping row without valid date")
                continue

            customers_affected: int | None
            try:
                customers_affected = clean_num_string(str(row["Number of Customers Affected"]))
            except ValueError:
                self.log.warning("customers_affected ValueError, trying to fix with AI")
                customers_affected = asyncio.run(self.ai.fix_number(str(row["Number of Customers Affected"])))

            demand_loss_mw: int | None
            try:
                demand_loss_mw = clean_num_string(str(row["Loss (megawatts)"]))
            except ValueError:
                self.log.warning("demand_loss_mw ValueError, trying to fix with AI")
                demand_loss_mw = asyncio.run(self.ai.fix_number(str(row["Loss (megawatts)"])))

            # Try to parse out the region from the utility name.
            # Sometimes the region is in parentheses at the end of the utility name.
            # Region names are always 2 to 6 letters long in uppercase.

            region = None

            if "NERC Region" in row:
                region = row["NERC Region"]
                utility_name = None
            else:
                utility_name = row["Utility/Power Pool (NERC Council)"].strip()
                if utility_name and utility_name[-1] == ")":
                    # Try to find the region in parentheses at the end of the utility name
                    match = re.search(r"\(([A-Z]{2,6})\)$", utility_name)
                    if match:
                        region = match.group(1)
                        utility_name = utility_name[: match.start()].strip()

            try:
                event = PowerOutageEvent(
                    date=row["Date"].strftime("%Y-%m-%d"),
                    # date=row["Date"],
                    time=row["Time"].strftime("%H:%M:%S"),
                    region=region,
                    area_affected=row["Area"],
                    customers_affected=customers_affected,
                    demand_loss_mw=demand_loss_mw,
                    outage_type=row["Type of Disturbance"],
                    utility_name=utility_name,
                    restoration_time=row["Restoration Time"],
                )
                self.data.append(event)
                self.log.info(f"SUCCESSFULLY PROCESSED ROW:\n{event}")
            except KeyError:
                self.log.exception("Error processing row, column mismatch")
            except ValueError:
                self.log.exception("Error processing row, value error")

    async def augment_data_with_ai(self) -> None:
        """Augment the data with AI."""
        self.log.info("Augmenting data with AI")

        background_tasks = set()

        async with asyncio.TaskGroup() as tg:
            for event in self.data:
                # Add the start datetime using the AI model
                task = tg.create_task(self.ai.add_start_datetime(event))
                background_tasks.add(task)

        # Wait for all the background tasks to complete
        await asyncio.gather(*background_tasks)

        background_tasks = set()

        async with asyncio.TaskGroup() as tg:
            for event in self.data:
                # Add the restored datetime using the AI model
                task = tg.create_task(self.ai.add_restored_datetime(event))
                background_tasks.add(task)

        # Wait for all the background tasks to complete
        await asyncio.gather(*background_tasks)

        # Get the results from the background tasks and update the data
        results = [task.result() for task in background_tasks]

        self.data = []
        for event in results:
            self.data.append(await self.get_duration_minutes(event))

    async def get_duration_minutes(self, event: PowerOutageEvent) -> PowerOutageEvent:
        """Calculate the duration of the outage in minutes."""
        self.log.info(f"Calculating duration in minutes for event: {event}")

        if event.start_datetime is None or event.restored_datetime is None:
            self.log.info("Cannot calculate duration without start and restored datetimes")
            return event

        # Calculate the duration in minutes
        start: datetime = datetime.fromisoformat(event.start_datetime)
        end: datetime = datetime.fromisoformat(event.restored_datetime)
        duration = end - start
        event.duration_minutes = int(duration.total_seconds() / 60)

        self.log.info(f"Calculated duration in minutes: {event.duration_minutes}")

        return event

    async def output_results(self) -> None:
        """Output the results."""
        self.log.info("Outputting results as a CSV")

        # Output the results as a csv into the data/normalized directory
        output_path = (
            Path(NORMALIZED_DATA_PATH)
            / f"{YEAR_RANGE.start}{NORMALIZED_SUFFIX}-{YEAR_RANGE.stop}{NORMALIZED_SUFFIX}.csv"
        )

        with output_path.open("w") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=PowerOutageEvent.model_fields.keys(),
                quotechar='"',
                quoting=csv.QUOTE_STRINGS,
            )
            writer.writeheader()

            for event in self.data:
                writer.writerow(event.model_dump())

        self.log.info("Outputting results as a human readable table")

        # Output the results as a human readable table
        table = Table(title="Power Outages")
        table.add_column("Start time")
        table.add_column("Restored time")
        table.add_column("Duration (minutes)")
        table.add_column("Outage Type")
        table.add_column("Region")
        table.add_column("Area Affected")
        table.add_column("Utility Name")
        table.add_column("Demand Loss (MW)")
        table.add_column("Customers Affected")

        for event in self.data:
            # Log the results in a human readable ASCII table
            table.add_row(
                str(event.start_datetime),
                str(event.restored_datetime),
                str(event.duration_minutes),
                event.outage_type,
                event.region,
                event.area_affected,
                event.utility_name,
                str(event.demand_loss_mw),
                str(event.customers_affected),
            )

        console = Console(color_system="standard")
        console.print(table)
