"""Contains classes/methods that will use the AI models to automatically parse the data."""

import logging
import os

import dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from poweroutageanalysis.types import PowerOutageEvent
from poweroutageanalysis.util import check_for_na_value

dotenv.load_dotenv()

AI_MODEL = "gpt-4o-mini-2024-07-18"


class DateResponse(BaseModel):
    """The response from the AI model."""

    datetime: str


class NumberResponse(BaseModel):
    """The response from the AI model."""

    number: int


class PowerOutageAI:
    """Class with methods that implement fixes to the data using the AI models."""

    def __init__(self) -> None:
        """Initialize the PowerOutageAI class."""
        self.log = logging.getLogger(__name__)
        self.log.info("Initializing PowerOutageAI")
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def add_start_datetime(self, event: PowerOutageEvent) -> PowerOutageEvent:
        """Add start_datetime to the PowerOutageEvent using the AI model."""
        self.log.info(f"Adding start datetime to event: {event}")

        # Use the AI model to add the start datetime
        system_prompt = """Below are is a date string and a time string. Please return the ISO 8601 datetime that represents the values from both the date and time strings. The new datetime should not have a time zone specified. The input date string is in the format m/d/YY and the input time string is in the format HH:MM a.m. or HH:MM p.m. If the input time is not provided, assume it is 00:00:00.
        """  # noqa: E501

        data_message = f"Date: {event.date}\nTime: {event.time}"

        response = await self.client.beta.chat.completions.parse(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_message},
            ],
            response_format=DateResponse,
        )
        message = response.choices[0].message

        if message.parsed:
            event.start_datetime = message.parsed.datetime
            self.log.info(f"Added start datetime to event: {event}")
        else:
            self.log.error(f"Failed to add start datetime to event: {event}")

        return event

    async def add_restored_datetime(self, event: PowerOutageEvent) -> PowerOutageEvent:
        """Add restored_datetime to the PowerOutageEvent using the AI model."""
        self.log.info(f"Adding restored datetime to event: {event}")

        # Try a simple check to handle when there is no listed restoration time
        check = check_for_na_value(event.restoration_time)
        if check is None:
            self.log.info("No restoration time provided")
            return event

        # Use the AI model to add the restored datetime
        system_prompt = """
        Below is a string that represents the restoration date and time for a power outage event. The string is written in English and needs to be converted to a ISO 8601 datetime.

        Please return the ISO 8601 datetime that represents the restoration date and time, considering the following:
        - The restoration datetime should be less than 6 months after the start date of the event.
        - The input string is in the format 'HH:MM a.m./p.m. Month D', e.g., '6:00 a.m. June 2', but might be in a different format. We have to do our best to parse it.
        - Use the start date's year for the restoration datetime, unless the restoration date is earlier than the start date. In that case, assume the restoration occurred in the following year.
        - The output datetime should not have a time zone specified.
        - If the restoration time is not provided, and only the date is present, assume the time is 23:59:59.
        """  # noqa: E501

        data_message = f"Start Date: {event.date}\nRestoration Time: {event.restoration_time}"

        response = await self.client.beta.chat.completions.parse(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_message},
            ],
            response_format=DateResponse,
        )
        message = response.choices[0].message

        if message.parsed:
            event.restored_datetime = message.parsed.datetime
            self.log.info(f"Added restored datetime to event: {event}")
        else:
            self.log.error(f"Failed to add restored datetime to event: {event}")

        return event

    async def fix_number(self, value: str) -> int | None:
        """Fix a number using the AI model."""
        self.log.info(f"Fixing number: {value}")

        # Use the AI model to fix the number
        system_prompt = """Below is a string that is suppsed to represent an integer. Please return the correct numeric value as an integer.
        - If the string specifies a range, return the highest value in the range.
        - If the string lists an English word for the number or approximate number, return the numeric value closest to that representation.
        - If the string is empty or specifies that the value is not available, return -1.
        """  # noqa: E501

        response = await self.client.beta.chat.completions.parse(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": value},
            ],
            response_format=NumberResponse,
        )
        message = response.choices[0].message

        if message.parsed:
            fixed_number = int(message.parsed.number)
            self.log.info(f"Fixed number: {fixed_number}")
        else:
            self.log.error(f"Failed to fix number: {value}")
            fixed_number = None

        if fixed_number == -1:
            return None
        return fixed_number
