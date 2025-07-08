# PubMed Papers Fetcher

Fetch PubMed papers with at least one non-academic (pharma/biotech) author and export to CSV.

## Setup

```bash
git clone https://github.com/your-username/pubmed-papers-fetcher.git
cd pubmed-papers-fetcher
poetry install
```

## Usage

```bash
poetry run get-papers-list "your pubmed query" -d -f output.csv
```

## Options

- `-d`: Enable debug mode
- `-f`: CSV output filename

## Example

```bash
poetry run get-papers-list "cancer immunotherapy" -f results.csv
```
