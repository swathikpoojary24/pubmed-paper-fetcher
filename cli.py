import argparse
import csv
from papers_fetcher.fetcher import fetch_pubmed_ids, fetch_details, PaperInfo

def write_csv(papers: list[PaperInfo], filename: str) -> None:
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "PubmedID",
            "Title",
            "Publication Date",
            "Non-academic Author(s)",
            "Company Affiliation(s)",
            "Corresponding Author Email"
        ])
        for p in papers:
            writer.writerow([
                p.pubmed_id,
                p.title,
                p.publication_date,
                "; ".join(p.non_academic_authors),
                "; ".join(p.company_affiliations),
                p.corresponding_email or ""
            ])

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch PubMed papers with pharma/biotech authors")
    parser.add_argument("query", help="PubMed query string")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-f", "--file", type=str, help="Filename to save CSV output")
    args = parser.parse_args()

    if args.debug:
        print("[DEBUG] Fetching PubMed IDs...")

    ids = fetch_pubmed_ids(args.query, debug=args.debug)
    papers = fetch_details(ids, debug=args.debug)

    if args.file:
        write_csv(papers, args.file)
        print(f"Results saved to {args.file}")
    else:
        for p in papers:
            print(f"{p.pubmed_id}: {p.title} ({p.publication_date})")
            print(f"  Authors: {', '.join(p.non_academic_authors)}")
            print(f"  Companies: {', '.join(p.company_affiliations)}")
            print(f"  Email: {p.corresponding_email}")
            print("-" * 80)

if __name__ == "__main__":
    main()
