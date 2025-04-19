"""
Main module for the PubMed Pharma Papers command-line tool.
"""
import argparse
import sys
from typing import List

from pubmed_pharma_papers.pubmed_client import PubMedClient
from pubmed_pharma_papers.paper_processor import PaperProcessor


def main() -> int:
    """
    Main entry point for the program.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Find PubMed papers with authors affiliated with pharmaceutical companies."
    )
    parser.add_argument(
        "query",
        help="PubMed search query"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Print debug information"
    )
    parser.add_argument(
        "-f", "--file",
        help="File path to save results (if not provided, prints to console)"
    )
    parser.add_argument(
        "-m", "--max-results",
        type=int,
        default=100,
        help="Maximum number of results to fetch (default: 100)"
    )

    args = parser.parse_args()

    try:
        if args.debug:
            print(f"Query: {args.query}")
            print(f"Output file: {args.file if args.file else 'console'}")

        # Initialize the PubMed client and paper processor
        pubmed_client = PubMedClient()
        paper_processor = PaperProcessor(debug=args.debug)

        # Search for papers
        pmids = pubmed_client.search(args.query, max_results=args.max_results, debug=args.debug)

        if not pmids:
            print("No papers found matching the query.")
            return 0

        # Fetch paper details
        papers = pubmed_client.fetch_details(pmids, debug=args.debug)

        # Process papers to find those with pharma affiliations
        processed_papers = paper_processor.process_papers(papers)

        # Export results
        if args.file:
            paper_processor.export_to_csv(processed_papers, args.file)
            print(f"Results saved to {args.file}")
        else:
            # Print to console
            csv_content = paper_processor.export_to_csv(processed_papers)
            print(csv_content)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
