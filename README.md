# PubMed Paper Fetcher

## Overview

This Python CLI tool searches PubMed for research papers and filters them to find those with authors affiliated with pharmaceutical or biotech companies. Results can be output to the console or a CSV file. It leverages PubMed's API, custom affiliation heuristics, and is managed with Poetry.

## Features

* **PubMed Integration:** Fetches data via PubMed ESearch and EFetch APIs.
* **Smart Filtering:** Identifies non-academic (pharma/biotech) author affiliations using defined keywords.
* **Flexible Queries:** Supports full PubMed query syntax.
* **Output Options:** Displays results in console or exports to a structured CSV file.
* **Robust & Typed:** Built with error handling and Python type hints for reliability.

## Installation

1.  **Prerequisites:** Ensure Python 3.10+ and [Poetry](https://python-poetry.org/) are installed.
2.  **Clone/Download:** Get the project from its [GitHub repository](https://github.com/swathikpoojary24/pubmed-paper-fetcher.git).
    ```bash
    git clone [https://github.com/swathikpoojary24/pubmed-paper-fetcher.git](https://github.com/swathikpoojary24/pubmed-paper-fetcher.git)
    cd pubmed-paper-fetcher # Or navigate to your unzipped folder
    ```
3.  **Install Dependencies:** From the project root (where `pyproject.toml` is):
    ```bash
    poetry install
    ```
    *Remember to close and reopen your terminal after Poetry installation.*

## Usage

Run the tool using `poetry run get-papers-list` with your desired arguments.

```bash
poetry run get-papers-list <query> --email <your_email> [--file <filename>] [--debug]
