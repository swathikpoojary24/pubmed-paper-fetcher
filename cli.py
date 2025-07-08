import argparse
import csv
import sys
from typing import List

from papers_fetcher.fetcher import fetch_pubmed_ids, fetch_and_parse_paper_details, PaperInfo

def write_csv(papers: List[PaperInfo], filename: str) -> None:
    csv_headers = [
        "PubmedID",
        "Title",
        "Publication Date",
        "Non-academic Author(s)",
        "Company Affiliation(s)",
        "Corresponding Author Email"
    ]

    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            for p in papers:
                writer.writerow([
                    p.pubmed_id,
                    p.title,
                    p.publication_date,
                    "; ".join(p.non_academic_authors),
                    "; ".join(p.company_affiliations),
                    p.corresponding_email if p.corresponding_email else ""
                ])
    except IOError as e:
        print(f"Error: Could not write to file '{filename}'. Reason: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while writing CSV: {e}", file=sys.stderr)


def print_to_console(papers: List[PaperInfo]) -> None:
    if not papers:
        print("No papers found matching the criteria.")
        return

    for p in papers:
        print(f"PubmedID: {p.pubmed_id}")
        print(f"Title: {p.title}")
        print(f"Publication Date: {p.publication_date}")
        print(f"Non-academic Author(s): {'; '.join(p.non_academic_authors)}")
        print(f"Company Affiliation(s): {'; '.join(p.company_affiliations)}")
        print(f"Corresponding Author Email: {p.corresponding_email if p.corresponding_email else 'N/A'}")
        print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch PubMed papers with at least one author affiliated "
                    "with a pharmaceutical or biotech company.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="The PubMed query string. Supports PubMed's full query syntax, e.g., '\"cancer immunotherapy\"[Title/Abstract] AND 2020:2024[PDAT]'"
    )
    
    parser.add_argument(
        "-e", "--email",
        type=str,
        required=True,
        help="Your email address (required by NCBI for Entrez API usage)."
    )

    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug output to print verbose information during execution."
    )
    
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Specify the filename to save the results as a CSV file. If not provided, output will be printed to the console."
    )
    
    args = parser.parse_args()

    if args.debug:
        print(f"[DEBUG] Starting paper fetch for query: '{args.query}'", file=sys.stderr)
        print(f"[DEBUG] Using email: '{args.email}'", file=sys.stderr)

    try:
        pubmed_ids = fetch_pubmed_ids(args.query, debug=args.debug)
        if not pubmed_ids:
            print(f"No PubMed IDs found for query: '{args.query}'", file=sys.stderr)
            sys.exit(1)

        papers = fetch_and_parse_paper_details(pubmed_ids, debug=args.debug)

        if not papers:
            print("No papers found with non-academic (pharma/biotech) affiliations matching the criteria.", file=sys.stderr)
            sys.exit(0)

        if args.file:
            write_csv(papers, args.file)
            print(f"Results successfully saved to '{args.file}'")
        else:
            print_to_console(papers)

    except Exception as e:
        print(f"An error occurred during execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
