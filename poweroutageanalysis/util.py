"""Contains utility functions for the poweroutageanalysis package."""


def clean_num_string(value_str: str) -> int | None:
    """Remove leading and trailing whitespace from a string."""
    value_str = remove_commas(value_str.strip())
    value_str = remove_approx(value_str.strip())
    value_str = extract_highest_from_range(value_str.strip())
    value_str = check_for_na_value(value_str.strip())

    if value_str is None:
        return None
    return int(value_str)


def check_for_na_value(value: str) -> str | None:
    """Check if a value is 'NA', 'N/A', 'None', or an empty string."""
    if value.lower() in ["na", "n/a", "none", ""]:
        return None
    return value


def remove_commas(value: str) -> str:
    """Remove commas from a string."""
    return value.replace(",", "")


def remove_approx(value: str) -> str:
    """Remove the "Approx." string from a string."""
    return value.replace("Approx.", "")


def extract_highest_from_range(value: str) -> str:
    """Split a string on a dash and return the latter value."""
    return value.split("-")[-1]
