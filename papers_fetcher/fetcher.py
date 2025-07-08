from typing import List, Optional
import requests
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass

@dataclass
class PaperInfo:
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_email: Optional[str]

def is_non_academic_affiliation(affiliation: str) -> bool:
    academic_keywords = [
        "university", "institute", "college", "school", "department",
        "faculty", "hospital", "center", "centre", "academy"
    ]
    affiliation_lower = affiliation.lower()
    return not any(word in affiliation_lower for word in academic_keywords)

def extract_emails(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", text)

def fetch_pubmed_ids(query: str, debug: bool = False) -> List[str]:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": "100", "retmode": "xml"}
    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ids = [id_elem.text for id_elem in root.findall("./IdList/Id")]
    if debug:
        print(f"[DEBUG] Found {len(ids)} PubMed IDs")
    return ids

def fetch_details(pubmed_ids: List[str], debug: bool = False) -> List[PaperInfo]:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": ",".join(pubmed_ids), "retmode": "xml"}
    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    papers: List[PaperInfo] = []

    for article in root.findall("./PubmedArticle"):
        pmid = article.findtext("./MedlineCitation/PMID")
        title = article.findtext("./MedlineCitation/Article/ArticleTitle") or "N/A"
        pub_date_node = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate")
        pub_date = "N/A"
        if pub_date_node is not None:
            year = pub_date_node.findtext("Year")
            medline_date = pub_date_node.findtext("MedlineDate")
            pub_date = year if year else (medline_date or "N/A")

        authors = article.findall("./MedlineCitation/Article/AuthorList/Author")
        non_academic_authors = []
        company_affiliations = []
        corresponding_email = None

        for author in authors:
            affiliation_info = author.find("./AffiliationInfo/Affiliation")
            if affiliation_info is not None:
                affiliation_text = affiliation_info.text or ""
                if is_non_academic_affiliation(affiliation_text):
                    last_name = author.findtext("LastName") or ""
                    fore_name = author.findtext("ForeName") or ""
                    full_name = f"{fore_name} {last_name}".strip()
                    non_academic_authors.append(full_name)
                    company_affiliations.append(affiliation_text)
                    emails = extract_emails(affiliation_text)
                    if emails and corresponding_email is None:
                        corresponding_email = emails[0]

        if non_academic_authors:
            papers.append(PaperInfo(
                pubmed_id=pmid,
                title=title,
                publication_date=pub_date,
                non_academic_authors=non_academic_authors,
                company_affiliations=company_affiliations,
                corresponding_email=corresponding_email
            ))

    return papers
