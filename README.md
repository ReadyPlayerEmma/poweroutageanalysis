# Power Outage Analysis

A Python package designed to analyze power outage trends using the Electric Disturbance Events (DOE-417) dataset from the U.S. Department of Energy.

## Data

The data used is from the U.S. Department of Energy website.

It seems that this data has a very inconsistent format over the years. The first thing I will be doing is trying to normalize the data into a consistent format. Unfortunately, no traditional methods will work due to the fields (including dates and times)sometimes being in plain English instead of any standardized format. So, we'll be using OpenAI's models to parse the unparseable.

### Electric Disturbance Events (DOE-417)
https://www.oe.netl.doe.gov/oe417.aspx
https://www.oe.netl.doe.gov/OE417_annual_summary.aspx

The original filenames are in the format YYYY_Annual_Summary.xls or YYYY_Annual_Summary.pdf

2000 and 2001 have been parsed out of the PDFs into the CSV files (using ChatGPT). This is due to the fact that only the PDF was available for those years.

All remaining years are in the Excel files.

## Prerequisites

- Python 3.12+
- Poetry
- OpenAI API token

## Installation of dependencies

In the project root, run:

```bash
poetry install
```

## Environment variables

Copy the `.env.example` file to `.env` and fill in the missing values with your own.

## Running the analysis

```bash
poetry run python -m poweroutageanalysis
```
