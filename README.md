# Power Outage Analysis

This project is a Python package designed to analyze power outages. It provides a class for analyzing power outages and a command-line interface for running the analysis.

## Data

The data used is from the U.S. Department of Energy website.

### Electric Disturbance Events (DOE-417)
https://www.oe.netl.doe.gov/oe417.aspx
https://www.oe.netl.doe.gov/OE417_annual_summary.aspx

The original filenames are in the format YYYY_Annual_Summary.xls or YYYY_Annual_Summary.pdf

2000 and 2001 have been parsed out of the PDFs into the CSV files (using ChatGPT). This is due to the fact that only the PDF was available for those years.

All remaining years are in the Excel files.

## Prerequisites

- Python 3.12+
- Poetry

## Installation of dependencies

In the project root, run:

```bash
poetry install
```

## Running the analysis

```bash
poetry run python -m poweroutageanalysis
```
