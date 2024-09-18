"""Define some types we will use throughout the project."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class PowerOutageEvent(BaseModel):
    """A power outage event."""

    # Date of outage (usually in the m/d/YY format), and always present
    date: str

    # Time of outage (usually in the HH:MM a.m. or HH:MM p.m. format), not always present
    time: str | None = None

    # "restoration time" string is an absolute mess that we need to parse to populate the restored datetime
    # It is not always present
    restoration_time: str | None = None

    # The cause of the outage (one of the only consistent and well-defined fields)
    outage_type: str

    # The NERC region affected by the outage
    # This is not directly present in the older files, but was sometimes appended to the utility name in parentheses
    region: str | None = None

    # The freeform "area affected" field value
    area_affected: str | None = None

    # The utility name that reported the outage (may not be consistent)
    utility_name: str | None = None

    # Metawatts of load affected (optional)
    demand_loss_mw: int | None = None

    # Number of customers affected
    customers_affected: int | None = None

    ### The following fields are the ones we will need to create by parsing out the messy data ###

    # The date and time the outage began (must be parsed out of the messy data)
    start_datetime: str | None = None

    # The date and time the outage ended (must be parsed out of the messy data if available)
    restored_datetime: str | None = None

    # The duration of the outage in minutes (calculated from start and end datetime)
    duration_minutes: int | None = None
