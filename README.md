# PubMed Paper Fetcher

## Overview

This Python command-line tool searches PubMed for research papers, specifically filtering them to identify those with authors affiliated with pharmaceutical or biotech companies. It supports PubMed's full query syntax and can output results to the console or save them as a detailed CSV file.

## Code Organization
The project is structured for clarity and maintainability:

pyproject.toml: Poetry's configuration, defining project metadata, dependencies, and the get-papers-list command entry point.

cli.py: The command-line interface (CLI) script; parses arguments and orchestrates the core logic.

papers_fetcher/: A Python package containing the core functionality.

papers_fetcher/__init__.py: Marks papers_fetcher as a package.

papers_fetcher/fetcher.py: Handles PubMed API interactions, XML parsing, and heuristic-based non-academic affiliation identification.

## Installation and Execution

1.  **Prerequisites:** Ensure Python 3.10+ and [Poetry](https://python-poetry.org/) are installed.
2.  **Install Dependencies:** From the project root (where `pyproject.toml` is):
    ```bash
    poetry install    
    ```
3.  **Execute Program:** Run using poetry run get-papers-list with your query and email.
    ```bash
    poetry run get-papers-list "YOUR_QUERY" --email "YOUR_EMAIL@example.com" [--file FILENAME.csv] [--debug]   
    ```
    
## Tools Used

Python 3.10+

Poetry: Dependency management.

argparse (Standard Library): CLI argument parsing.

Requests: HTTP requests to PubMed API.

xml.etree.ElementTree (Standard Library): XML parsing.

csv (Standard Library): CSV file handling.

Git & GitHub: Version control and hosting.

GitHub Codespaces:  Cloud development environment.

Large Language Models (LLMs): Assisted in project design, code generation, debugging, and documentation.
