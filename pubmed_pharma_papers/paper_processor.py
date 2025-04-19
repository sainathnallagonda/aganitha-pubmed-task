"""
Module for processing PubMed papers and identifying authors with pharmaceutical company affiliations.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import re
import csv
import io


class PaperProcessor:
    """Class for processing PubMed papers and identifying pharma-affiliated authors."""

    # Common pharmaceutical and biotech company terms for identification
    PHARMA_TERMS = {
        "pharma", "pharmaceutical", "biotech", "therapeutics", "bioscience", "laboratories",
        "biologics", "biopharma", "medicines", "biotherapeutics", "biosystems",
        "drug", "health", "medical", "diagnostics", "genomics"
    }

    # Academic institution terms to exclude
    ACADEMIC_TERMS = {
        "university", "college", "institute", "school", "academy", "hospital",
        "clinic", "medical center", "research center", "foundation", "laboratory",
        "national", "federal", "ministry", "department"
    }

    def __init__(self, debug: bool = False):
        """
        Initialize the paper processor.

        Args:
            debug: Whether to print debug information
        """
        self.debug = debug

    def is_pharma_affiliation(self, affiliation: str) -> bool:
        """
        Determine if an affiliation is from a pharmaceutical or biotech company.

        Args:
            affiliation: The affiliation string to check

        Returns:
            True if the affiliation appears to be from a pharma/biotech company
        """
        if not affiliation:
            return False

        # Convert to lowercase for case-insensitive matching
        affiliation_lower = affiliation.lower()

        # Check for academic terms first (negative signal)
        for term in self.ACADEMIC_TERMS:
            if term in affiliation_lower:
                return False

        # Look for pharmaceutical terms
        for term in self.PHARMA_TERMS:
            if term in affiliation_lower:
                # Check for company indicators
                if any(indicator in affiliation_lower for indicator in
                       [" inc", " corp", " co.", " ltd", " llc", "company", " sa", " ag", " gmbh"]):
                    return True

        # Check for common pharma company endings
        if re.search(r'(?:inc|corp|co\.|ltd|llc|gmbh|sa|ag|pty)\.?$', affiliation_lower.strip()):
            return True

        return False

    def extract_company_name(self, affiliation: str) -> str:
        """
        Extract the company name from an affiliation string.

        Args:
            affiliation: The affiliation string

        Returns:
            The extracted company name
        """
        # This is a simplified version - in a real application, this would be more sophisticated
        if not affiliation:
            return ""

        # Try to extract the company name before a comma or parenthesis
        match = re.search(r'^([^,\(]+)', affiliation)
        if match:
            return match.group(1).strip()

        return affiliation

    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers to identify those with pharma affiliations.

        Args:
            papers: List of paper dictionaries from PubMed

        Returns:
            List of papers with pharma affiliation information added
        """
        processed_papers = []

        for paper in papers:
            pharma_authors = []
            company_affiliations = set()
            corresponding_email = ""

            # Process authors and their affiliations
            for author in paper.get("authors", []):
                author_name = author.get("name", "")
                affiliations = author.get("affiliations", [])

                for affiliation in affiliations:
                    if self.is_pharma_affiliation(affiliation):
                        pharma_authors.append(author_name)
                        company_name = self.extract_company_name(affiliation)
                        if company_name:
                            company_affiliations.add(company_name)

                # Check if this is a corresponding author
                if author.get("is_corresponding", False) and author.get("email"):
                    corresponding_email = author.get("email")

            # Only include papers with at least one pharma-affiliated author
            if pharma_authors:
                processed_paper = {
                    "PubmedID": paper.get("pmid", ""),
                    "Title": paper.get("title", ""),
                    "Publication Date": paper.get("publication_date", ""),
                    "Non-academic Author(s)": "; ".join(pharma_authors),
                    "Company Affiliation(s)": "; ".join(company_affiliations),
                    "Corresponding Author Email": corresponding_email
                }
                processed_papers.append(processed_paper)

                if self.debug:
                    print(f"Found paper with pharma affiliations: {paper.get('title')}")

        return processed_papers

    def export_to_csv(self, papers: List[Dict[str, Any]], file_path: Optional[str] = None) -> Optional[str]:
        """
        Export processed papers to CSV.

        Args:
            papers: List of processed papers
            file_path: Path to save the CSV file, if None returns CSV as string

        Returns:
            CSV string if file_path is None, otherwise None
        """
        if not papers:
            if self.debug:
                print("No papers to export")
            return "" if file_path is None else None

        # Define CSV columns
        fieldnames = [
            "PubmedID", "Title", "Publication Date",
            "Non-academic Author(s)", "Company Affiliation(s)",
            "Corresponding Author Email"
        ]

        if file_path is None:
            # Return as string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(papers)
            return output.getvalue()
        else:
            # Write to file
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(papers)

            if self.debug:
                print(f"Exported {len(papers)} papers to {file_path}")

            return None