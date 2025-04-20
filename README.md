# PubMed Pharma Papers

This is a command-line Python tool I built to search PubMed for research papers and filter out the ones with at least one author affiliated with a pharma or biotech company.

The goal is to quickly get a list of such papers, extract basic info, and save everything into a CSV file.

---

## How it works

- It takes a search query (like "cancer therapy") and fetches results using the PubMed API.
- Then it checks each paper's authors to see if any of them are from non-academic places (based on email domains or keywords like "Inc.", "Ltd.", "Pharma", etc.).
- It also extracts the corresponding author's email if available.
- Finally, it saves all the filtered paper data into a CSV file.

---

## Files in the project

- `main.py` – entry point to run the script.
- `pubmed_client.py` – handles PubMed API requests.
- `paper_processor.py` – processes author info and applies the filtering logic.
- `results.csv` – sample output file.
- `tests/` – basic unit tests.
- `pyproject.toml` – project setup with Poetry.

---

