from typing import List, Optional
import requests
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
RETMAX_PAPERS = "200"

COMPANY_KEYWORDS = [
    "pharmaceutical", "pharma", "biotech", "biotechnology", "inc.", "llc",
    "corp.", "corporation", "co.", "company", "gmbh", "s.a.", "ag",
    "laboratories", "labs",
    "r&d", "research and development", "global", "solutions",
    "therapeutics", "diagnostics", "medicines", "drug discovery",
    "pfizer", "novartis", "roche", "gilead", "amgen", "moderna", "biontech",
    "astrazeneca", "johnson & johnson", "merck", "eli lilly", "sanofi"
]

ACADEMIC_KEYWORDS = [
    "university", "institute", "college", "school", "department",
    "faculty", "hospital", "medical center", "center for disease control",
    "public health", "federal agency", "nih", "cdc", "who", "fda", "ema"
]


@dataclass
class PaperInfo:
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_email: Optional[str]


def is_corporate_affiliation(affiliation: str) -> bool:
    affiliation_lower = affiliation.lower()

    has_company_keyword = any(word in affiliation_lower for word in COMPANY_KEYWORDS)
    has_academic_keyword = any(word in affiliation_lower for word in ACADEMIC_KEYWORDS)

    if has_company_keyword and not has_academic_keyword:
        return True
    
    return False


def extract_first_email_from_text(text: str) -> Optional[str]:
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return emails[0] if emails else None


def fetch_pubmed_ids(query: str, debug: bool = False) -> List[str]:
    params = {"db": "pubmed", "term": query, "retmax": RETMAX_PAPERS, "retmode": "xml"}
    try:
        resp = requests.get(PUBMED_ESEARCH_URL, params=params)
        resp.raise_for_status()
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
    if not pubmed_ids:
        if debug:
            print("[DEBUG] No PubMed IDs to fetch details for.")
        return []

    params = {"db": "pubmed", "id": ",".join(pubmed_ids), "retmode": "xml"}
    
    try:
        resp = requests.get(PUBMED_EFETCH_URL, params=params)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        
        filtered_papers: List[PaperInfo] = []

        for article in root.findall("./PubmedArticle"):
            pmid = article.findtext("./MedlineCitation/PMID") or "N/A"
            title = article.findtext("./MedlineCitation/Article/ArticleTitle") or "N/A"

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

            for author in article.findall("./MedlineCitation/Article/AuthorList/Author"):
                last_name = author.findtext("LastName")
                fore_name = author.findtext("ForeName")
                full_name = f"{fore_name or ''} {last_name or ''}".strip()

                affiliation_node = author.find("./AffiliationInfo/Affiliation")
                affiliation_text = affiliation_node.text if affiliation_node is not None else ""

                if is_corporate_affiliation(affiliation_text):
                    if full_name:
                        current_non_academic_authors.append(full_name)
                    if affiliation_text:
                        current_company_affiliations.append(affiliation_text)
            
            article_abstract_text = article.findtext("./MedlineCitation/Article/Abstract/AbstractText")
            article_other_fields_text = (
                article.findtext("./MedlineCitation/Article/ArticleTitle") + " " +
                article.findtext("./MedlineCitation/Article/AuthorList/Author/AffiliationInfo/Affiliation") + " " +
                (article_abstract_text if article_abstract_text else "")
            ) if article.findtext("./MedlineCitation/Article/AuthorList/Author/AffiliationInfo/Affiliation") else ""


            if article_other_fields_text:
                 current_corresponding_email = extract_first_email_from_text(article_other_fields_text)

            if current_non_academic_authors:
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
    except Exception as e:
        print(f"An unexpected error occurred during detail fetching/parsing for PubMed IDs {pubmed_ids}: {e}")
        return []
