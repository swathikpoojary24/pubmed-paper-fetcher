import argparse
import csv
import sys # Import sys for stderr
from typing import List

# Assuming your refactored fetcher is in papers_fetcher/fetcher.py
# (This import path needs to match your actual file structure)
from papers_fetcher.fetcher import fetch_pubmed_ids, fetch_and_parse_paper_details, PaperInfo

def write_csv(papers: List[PaperInfo], filename: str) -> None:
    """
    Writes a list of PaperInfo objects to a CSV file.

    Args:
        papers: A list of PaperInfo objects to write.
        filename: The name of the CSV file to create/overwrite.
    """
    # Define CSV column headers based on problem requirements
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
            writer.writerow(csv_headers) # Write the header row
            for p in papers:
                writer.writerow([
                    p.pubmed_id,
                    p.title,
                    p.publication_date,
                    # Join lists with '; ' as separator for clarity in CSV
                    "; ".join(p.non_academic_authors),
                    "; ".join(p.company_affiliations),
                    p.corresponding_email if p.corresponding_email else "" # Ensure empty string for None
                ])
    except IOError as e:
        print(f"Error: Could not write to file '{filename}'. Reason: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while writing CSV: {e}", file=sys.stderr)


def print_to_console(papers: List[PaperInfo]) -> None:
    """
    Prints a list of PaperInfo objects to the console.

    Args:
        papers: A list of PaperInfo objects to print.
    """
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
        print("-" * 80) # Separator for readability


def main() -> None:
    """
    Main function to parse arguments, fetch papers, and handle output.
    """
    parser = argparse.ArgumentParser(
        description="Fetch PubMed papers with at least one author affiliated "
                    "with a pharmaceutical or biotech company.",
        formatter_class=argparse.RawTextHelpFormatter # For better help formatting
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="The PubMed query string. Supports PubMed's full query syntax, e.g., '\"cancer immunotherapy\"[Title/Abstract] AND 2020:2024[PDAT]'"
    )
    
    parser.add_argument(
        "-e", "--email",
        type=str,
        required=True, # Make email required as per NCBI guidelines
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

    # Set NCBI Entrez email (crucial for API access)
    # This must be set before any Bio.Entrez calls.
    # While fetcher.py doesn't directly use Bio.Entrez.email, NCBI sometimes
    # checks the User-Agent, and a common practice is to pass it.
    # The refined fetcher.py should technically handle its own email if using Bio.Entrez.
    # If using requests directly as in your current fetcher.py,
    # the email is more for compliance/identification with NCBI, not necessarily
    # passed in every request. For robustness, if Bio.Entrez was used, this would be:
    # from Bio import Entrez
    # Entrez.email = args.email
    # For now, we'll just acknowledge it's passed as an arg but the fetcher.py
    # logic using 'requests' doesn't explicitly use it *in the request params*.
    # It's more about adhering to NCBI's policy for identifying users.

    if args.debug:
        print(f"[DEBUG] Starting paper fetch for query: '{args.query}'", file=sys.stderr)
        print(f"[DEBUG] Using email: '{args.email}'", file=sys.stderr)

    try:
        pubmed_ids = fetch_pubmed_ids(args.query, debug=args.debug)
        if not pubmed_ids:
            print(f"No PubMed IDs found for query: '{args.query}'", file=sys.stderr)
            sys.exit(1) # Exit with an error code

        papers = fetch_and_parse_paper_details(pubmed_ids, debug=args.debug)

        if not papers:
            print("No papers found with non-academic (pharma/biotech) affiliations matching the criteria.", file=sys.stderr)
            sys.exit(0) # Exit successfully if no filtered papers, but inform user

        if args.file:
            write_csv(papers, args.file)
            print(f"Results successfully saved to '{args.file}'")
        else:
            print_to_console(papers)

    except Exception as e:
        print(f"An error occurred during execution: {e}", file=sys.stderr)
        sys.exit(1) # Exit with an error code

if __name__ == "__main__":
    main()
