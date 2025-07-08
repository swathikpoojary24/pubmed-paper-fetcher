from typing import List, Optional
import requests
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass

# --- Constants for API and Heuristics ---
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
RETMAX_PAPERS = "200" # Increased retmax for more results, adjust as needed

# Heuristics for identifying company affiliations
# These keywords suggest a corporate/non-academic affiliation
COMPANY_KEYWORDS = [
    "pharmaceutical", "pharma", "biotech", "biotechnology", "inc.", "llc",
    "corp.", "corporation", "co.", "company", "gmbh", "s.a.", "ag",
    "laboratories", "labs", # Be careful, labs can be academic too,
                            # so combine with exclusion logic
    "r&d", "research and development", "global", "solutions",
    "therapeutics", "diagnostics", "medicines", "drug discovery",
    # Add specific company names if known to be prevalent
    "pfizer", "novartis", "roche", "gilead", "amgen", "moderna", "biontech",
    "astrazeneca", "johnson & johnson", "merck", "eli lilly", "sanofi"
]

# These keywords suggest an academic/hospital affiliation
ACADEMIC_KEYWORDS = [
    "university", "institute", "college", "school", "department",
    "faculty", "hospital", "medical center", "center for disease control",
    "public health", "federal agency", "nih", "cdc", "who", "fda", "ema"
]


@dataclass
class PaperInfo:
    """
    Represents a research paper with relevant extracted information.
    """
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_email: Optional[str]


def is_corporate_affiliation(affiliation: str) -> bool:
    """
    Determines if an affiliation string likely belongs to a pharmaceutical or biotech company.
    This heuristic looks for company-specific keywords and tries to exclude obvious academic ones.
    """
    affiliation_lower = affiliation.lower()

    # Check for strong company indicators
    has_company_keyword = any(word in affiliation_lower for word in COMPANY_KEYWORDS)

    # Check for strong academic indicators
    has_academic_keyword = any(word in affiliation_lower for word in ACADEMIC_KEYWORDS)

    # A more refined heuristic:
    # It's corporate if it has a company keyword AND it doesn't strongly look academic.
    # This helps filter out "University Hospital" or "Academic Research Labs"
    if has_company_keyword and not has_academic_keyword:
        return True
    
    # Edge case: If it contains words like "department of X" where X is a company name
    # or "division of X" this might still be academic, but for simplicity
    # we prioritize corporate keywords if academic ones are absent.

    return False


def extract_first_email_from_text(text: str) -> Optional[str]:
    """
    Extracts the first email address found in a given string.
    """
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return emails[0] if emails else None


def fetch_pubmed_ids(query: str, debug: bool = False) -> List[str]:
    """
    Fetches PubMed IDs based on a user-specified query.

    Args:
        query: The PubMed search query string.
        debug: If True, print debug information.

    Returns:
        A list of PubMed IDs (strings).

    Raises:
        requests.exceptions.RequestException: If the API call fails.
    """
    params = {"db": "pubmed", "term": query, "retmax": RETMAX_PAPERS, "retmode": "xml"}
    try:
        resp = requests.get(PUBMED_ESEARCH_URL, params=params)
        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        root = ET.fromstring(resp.text)
        ids = [id_elem.text for id_elem in root.findall("./IdList/Id") if id_elem.text]
        if debug:
            print(f"[DEBUG] Found {len(ids)} PubMed IDs for query: '{query}'")
        return ids
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PubMed IDs: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing XML for PubMed IDs: {e}")
        return []


def fetch_and_parse_paper_details(pubmed_ids: List[str], debug: bool = False) -> List[PaperInfo]:
    """
    Fetches detailed information for a list of PubMed IDs and parses it into PaperInfo objects.
    Filters papers to include only those with identified non-academic authors.

    Args:
        pubmed_ids: A list of PubMed IDs.
        debug: If True, print debug information.

    Returns:
        A list of PaperInfo objects for papers with non-academic authors.

    Raises:
        requests.exceptions.RequestException: If the API call fails.
    """
    if not pubmed_ids:
        if debug:
            print("[DEBUG] No PubMed IDs to fetch details for.")
        return []

    # PubMed efetch allows fetching multiple IDs at once, comma-separated
    params = {"db": "pubmed", "id": ",".join(pubmed_ids), "retmode": "xml"}
    
    try:
        resp = requests.get(PUBMED_EFETCH_URL, params=params)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        
        filtered_papers: List[PaperInfo] = []

        for article in root.findall("./PubmedArticle"):
            pmid = article.findtext("./MedlineCitation/PMID") or "N/A"
            title = article.findtext("./MedlineCitation/Article/ArticleTitle") or "N/A"

            # Extract publication date
            pub_date = "N/A"
            pub_date_node = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate")
            if pub_date_node is not None:
                year = pub_date_node.findtext("Year")
                month = pub_date_node.findtext("Month")
                day = pub_date_node.findtext("Day")
                medline_date = pub_date_node.findtext("MedlineDate")

                if year:
                    pub_date = f"{year}"
                    if month:
                        pub_date += f"-{month}"
                        if day:
                            pub_date += f"-{day}"
                elif medline_date:
                    pub_date = medline_date

            current_non_academic_authors: List[str] = []
            current_company_affiliations: List[str] = []
            current_corresponding_email: Optional[str] = None

            # Look for authors in AuthorList
            for author in article.findall("./MedlineCitation/Article/AuthorList/Author"):
                last_name = author.findtext("LastName")
                fore_name = author.findtext("ForeName")
                full_name = f"{fore_name or ''} {last_name or ''}".strip()

                # Check affiliation
                affiliation_node = author.find("./AffiliationInfo/Affiliation")
                affiliation_text = affiliation_node.text if affiliation_node is not None else ""

                if is_corporate_affiliation(affiliation_text):
                    if full_name: # Ensure we have a name
                        current_non_academic_authors.append(full_name)
                    if affiliation_text: # Ensure we have an affiliation to add
                        current_company_affiliations.append(affiliation_text)
            
            # Check for corresponding author email in the article itself, often in GrantList or other sections
            # This is a more generalized approach as corresponding author email isn't always tied to a single author's affiliation node.
            # PubMed XML doesn't have a direct 'corresponding_author_email' field, so we parse from text.
            # We'll prioritize the first email found anywhere if it fits
            article_abstract_text = article.findtext("./MedlineCitation/Article/Abstract/AbstractText")
            article_other_fields_text = (
                article.findtext("./MedlineCitation/Article/ArticleTitle") + " " +
                article.findtext("./MedlineCitation/Article/AuthorList/Author/AffiliationInfo/Affiliation") + " " +
                (article_abstract_text if article_abstract_text else "") # Add abstract if exists
            ) if article.findtext("./MedlineCitation/Article/AuthorList/Author/AffiliationInfo/Affiliation") else ""


            if article_other_fields_text:
                 current_corresponding_email = extract_first_email_from_text(article_other_fields_text)

            # Filter: Only include papers with at least one non-academic author found
            if current_non_academic_authors:
                # Deduplicate company affiliations and non-academic authors if necessary
                # (due to multiple authors from same company)
                unique_company_affiliations = list(set(current_company_affiliations))
                unique_non_academic_authors = list(set(current_non_academic_authors))

                filtered_papers.append(PaperInfo(
                    pubmed_id=pmid,
                    title=title,
                    publication_date=pub_date,
                    non_academic_authors=unique_non_academic_authors,
                    company_affiliations=unique_company_affiliations,
                    corresponding_email=current_corresponding_email
                ))
            elif debug:
                print(f"[DEBUG] Paper {pmid}: No non-academic authors found based on heuristics.")

        if debug:
            print(f"[DEBUG] Fetched details for {len(pubmed_ids)} papers. Filtered down to {len(filtered_papers)} with non-academic authors.")
        return filtered_papers
    except requests.exceptions.RequestException as e:
        print(f"Error fetching paper details: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing XML for paper details: {e}")
        return []
    except Exception as e: # Catch any other unexpected errors during parsing
        print(f"An unexpected error occurred during detail fetching/parsing for PubMed IDs {pubmed_ids}: {e}")
        return []
