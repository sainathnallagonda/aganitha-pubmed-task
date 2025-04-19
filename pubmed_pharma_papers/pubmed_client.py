"""
PubMed client module that handles API calls to the PubMed API.
"""
from typing import Dict, List, Any, Optional
import urllib.parse
import time
import requests
import xml.etree.ElementTree as ET
import re  # Add this import for regex


class PubMedClient:
    """Client for interacting with the PubMed API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def __init__(self, tool: str = "pubmed-pharma-papers", email: str = "your-email@example.com"):
        """
        Initialize the PubMed client.

        Args:
            tool: Name of the tool using the API
            email: Email address of the user
        """
        self.tool = tool
        self.email = email

    def search(self, query: str, max_results: int = 100, debug: bool = False) -> List[str]:
        """
        Search for papers in PubMed using the provided query.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            debug: Whether to print debug information

        Returns:
            List of PubMed IDs matching the query
        """
        if debug:
            print(f"Searching PubMed for: {query}")

        # Encode query for URL
        encoded_query = urllib.parse.quote(query)

        # Construct search URL
        search_url = f"{self.BASE_URL}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
            "tool": self.tool,
            "email": self.email
        }

        # Make the search request
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors

        search_results = response.json()

        if debug:
            print(f"Found {len(search_results.get('esearchresult', {}).get('idlist', []))} papers")

        # Extract IDs from search results
        id_list = search_results.get("esearchresult", {}).get("idlist", [])
        return id_list

    def fetch_details(self, pmid_list: List[str], debug: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch detailed information for a list of PubMed IDs.

        Args:
            pmid_list: List of PubMed IDs
            debug: Whether to print debug information

        Returns:
            List of dictionaries containing paper details
        """
        if not pmid_list:
            return []

        if debug:
            print(f"Fetching details for {len(pmid_list)} papers")

        # Construct fetch URL
        fetch_url = f"{self.BASE_URL}efetch.fcgi"

        # Split into chunks of 100 IDs to avoid URL length limitations
        chunk_size = 100
        all_papers = []

        for i in range(0, len(pmid_list), chunk_size):
            chunk = pmid_list[i:i + chunk_size]

            params = {
                "db": "pubmed",
                "id": ",".join(chunk),
                "retmode": "xml",
                "tool": self.tool,
                "email": self.email
            }

            # Make the fetch request
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()

            # Parse the XML response and extract paper details
            papers = self._parse_papers(response.text, debug)
            all_papers.extend(papers)

            # Be nice to the API and wait a bit between requests
            if i + chunk_size < len(pmid_list):
                time.sleep(0.5)

        return all_papers

    def _parse_papers(self, xml_content: str, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Parse XML content to extract paper details.

        Args:
            xml_content: XML content from PubMed
            debug: Whether to print debug information

        Returns:
            List of dictionaries containing paper details
        """
        papers = []

        try:
            # Parse XML content
            root = ET.fromstring(xml_content)

            # Find all PubmedArticle elements
            articles = root.findall(".//PubmedArticle")

            for article in articles:
                paper = {}

                # Extract PubMed ID
                pmid_elem = article.find(".//PMID")
                if pmid_elem is not None:
                    paper["pmid"] = pmid_elem.text
                else:
                    continue  # Skip if no PMID

                # Extract title
                title_elem = article.find(".//ArticleTitle")
                if title_elem is not None:
                    paper["title"] = title_elem.text
                else:
                    paper["title"] = ""

                # Extract publication date
                pub_date = ""
                pub_date_elem = article.find(".//PubDate")
                if pub_date_elem is not None:
                    year = pub_date_elem.findtext("Year", "")
                    month = pub_date_elem.findtext("Month", "")
                    day = pub_date_elem.findtext("Day", "")

                    if year:
                        pub_date = year
                        if month:
                            pub_date = f"{month} {pub_date}"
                            if day:
                                pub_date = f"{day} {pub_date}"

                paper["publication_date"] = pub_date

                # Extract authors and their affiliations
                authors = []
                author_list = article.find(".//AuthorList")

                if author_list is not None:
                    for author_elem in author_list.findall("Author"):
                        author = {}

                        # Get author name
                        last_name = author_elem.findtext("LastName", "")
                        fore_name = author_elem.findtext("ForeName", "")
                        initials = author_elem.findtext("Initials", "")

                        if last_name:
                            if fore_name:
                                author["name"] = f"{fore_name} {last_name}"
                            elif initials:
                                author["name"] = f"{initials} {last_name}"
                            else:
                                author["name"] = last_name
                        else:
                            # If no individual name parts, try CollectiveName
                            collective_name = author_elem.findtext("CollectiveName", "")
                            if collective_name:
                                author["name"] = collective_name
                            else:
                                continue  # Skip author with no name

                        # Get affiliations
                        affiliations = []

                        # Check for AffiliationInfo elements (newer format)
                        for aff_info in author_elem.findall(".//AffiliationInfo"):
                            aff_text = aff_info.findtext("Affiliation", "")
                            if aff_text:
                                affiliations.append(aff_text)

                        # If no AffiliationInfo found, look for direct Affiliation element (older format)
                        if not affiliations:
                            aff_text = author_elem.findtext("Affiliation", "")
                            if aff_text:
                                affiliations.append(aff_text)

                        author["affiliations"] = affiliations

                        # Check for corresponding author
                        # PubMed doesn't consistently mark corresponding authors, but we can check
                        # for EqualContrib attribute or look for author with email
                        author["is_corresponding"] = False
                        author["email"] = ""

                        # Try to find email in identifiers
                        for identifier in author_elem.findall(".//Identifier"):
                            if identifier.get("Source") == "email":
                                author["email"] = identifier.text
                                author["is_corresponding"] = True
                                break

                        # Sometimes emails are included in the affiliation text
                        if not author["email"]:
                            for aff in affiliations:
                                email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', aff)
                                if email_match:
                                    author["email"] = email_match.group(1)
                                    author["is_corresponding"] = True
                                    break

                        authors.append(author)

                paper["authors"] = authors
                papers.append(paper)

        except ET.ParseError as e:
            if debug:
                print(f"Error parsing XML: {e}")

        if debug and not papers:
            print("No papers were successfully parsed from the XML")

        return papers