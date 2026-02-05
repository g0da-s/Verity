"""PubMed API wrapper for searching and fetching scientific studies.

Uses NCBI's E-utilities API (Entrez) to search PubMed for health-related studies.
Requires email address for NCBI rate limiting compliance.
"""

import asyncio
import re
from typing import List, Dict, Any
from datetime import datetime
from Bio import Entrez
from app.config import settings
from app.models.state import Study


class PubMedTool:
    """Wrapper for PubMed E-utilities API.

    Handles searching, fetching, and parsing study metadata from PubMed.
    Implements rate limiting to comply with NCBI guidelines (3 requests/second).
    """

    def __init__(self):
        """Initialize PubMed tool with user email."""
        # NCBI requires email for identification
        Entrez.email = settings.pubmed_email

        # Rate limiting: NCBI allows 3 requests/second without API key
        self.rate_limit_delay = 0.34  # ~3 requests per second
        self.last_request_time = 0.0

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = asyncio.get_event_loop().time()

    async def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance"
    ) -> List[str]:
        """Search PubMed and return list of PubMed IDs.

        Args:
            query: Search query (e.g., "creatine muscle strength meta-analysis")
            max_results: Maximum number of results to return
            sort: Sort order ("relevance" or "pub_date")

        Returns:
            List of PubMed IDs as strings

        Raises:
            Exception: If PubMed API request fails
        """
        await self._rate_limit()

        try:
            # Run synchronous Entrez call in thread pool
            loop = asyncio.get_event_loop()
            handle = await loop.run_in_executor(
                None,
                lambda: Entrez.esearch(
                    db="pubmed",
                    term=query,
                    retmax=max_results,
                    sort=sort,
                    usehistory="y"
                )
            )

            record = Entrez.read(handle)
            handle.close()

            return record.get("IdList", [])

        except Exception as e:
            raise Exception(f"PubMed search failed: {str(e)}")

    async def fetch_details(self, pubmed_ids: List[str]) -> List[Study]:
        """Fetch full metadata for a list of PubMed IDs.

        Args:
            pubmed_ids: List of PubMed IDs to fetch

        Returns:
            List of Study objects with metadata

        Raises:
            Exception: If PubMed API request fails
        """
        if not pubmed_ids:
            return []

        await self._rate_limit()

        try:
            # Fetch records
            loop = asyncio.get_event_loop()
            handle = await loop.run_in_executor(
                None,
                lambda: Entrez.efetch(
                    db="pubmed",
                    id=",".join(pubmed_ids),
                    rettype="medline",
                    retmode="xml"
                )
            )

            records = Entrez.read(handle)
            handle.close()

            # Parse each record into Study objects
            studies = []
            for record in records.get("PubmedArticle", []):
                study = self._parse_record(record)
                if study:
                    studies.append(study)

            return studies

        except Exception as e:
            raise Exception(f"PubMed fetch failed: {str(e)}")

    def _parse_record(self, record: Dict[str, Any]) -> Study | None:
        """Parse a PubMed XML record into a Study object.

        Args:
            record: PubMed article record from Entrez

        Returns:
            Study object or None if parsing fails
        """
        try:
            article = record.get("MedlineCitation", {}).get("Article", {})
            medline = record.get("MedlineCitation", {})

            # Extract PubMed ID
            pubmed_id = str(medline.get("PMID", ""))

            # Extract title
            title = article.get("ArticleTitle", "")

            # Extract authors
            authors_list = article.get("AuthorList", [])
            authors = self._format_authors(authors_list)

            # Extract journal
            journal = article.get("Journal", {}).get("Title", "Unknown Journal")

            # Extract year
            pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            year = self._extract_year(pub_date)

            # Extract abstract
            abstract_sections = article.get("Abstract", {}).get("AbstractText", [])
            abstract = self._format_abstract(abstract_sections)

            # Determine study type from abstract/title
            study_type = self._identify_study_type(title, abstract)

            # Estimate sample size from abstract
            sample_size = self._extract_sample_size(abstract)

            # Build PubMed URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"

            return Study(
                pubmed_id=pubmed_id,
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                study_type=study_type,
                sample_size=sample_size,
                abstract=abstract,
                url=url
            )

        except Exception as e:
            # Skip records that fail to parse
            return None

    def _format_authors(self, authors_list: List[Dict]) -> str:
        """Format author list as comma-separated string.

        Args:
            authors_list: List of author dictionaries from PubMed

        Returns:
            Formatted author string (e.g., "Smith J, Jones K, Williams L")
        """
        if not authors_list:
            return "Unknown"

        # Take first 3 authors
        authors = []
        for author in authors_list[:3]:
            last_name = author.get("LastName", "")
            initials = author.get("Initials", "")
            if last_name:
                authors.append(f"{last_name} {initials}".strip())

        # Add "et al." if more than 3 authors
        if len(authors_list) > 3:
            authors.append("et al.")

        return ", ".join(authors) if authors else "Unknown"

    def _extract_year(self, pub_date: Dict) -> int:
        """Extract publication year from PubDate dict.

        Args:
            pub_date: PubDate dictionary from PubMed

        Returns:
            Publication year as integer, or current year if not found
        """
        year = pub_date.get("Year")
        if year:
            try:
                return int(year)
            except (ValueError, TypeError):
                pass

        return datetime.now().year

    def _format_abstract(self, abstract_sections: List) -> str:
        """Extract Results and Conclusions from a structured abstract.

        For structured abstracts (with labeled sections), only Results and
        Conclusions are kept — these contain the findings the synthesis agent
        needs. Background, Objectives, and Methods are redundant: the LLM
        already knows the claim context, and study_type/sample_size are stored
        as separate fields.

        For unstructured abstracts (plain text, no labels), the full text is
        returned as a fallback.

        Args:
            abstract_sections: List of abstract text sections from PubMed

        Returns:
            Extracted abstract text
        """
        if not abstract_sections:
            return "No abstract available"

        if not isinstance(abstract_sections, list):
            return str(abstract_sections)

        # Check if any sections have labels (structured abstract)
        has_labels = any(
            hasattr(section, "attributes") and "Label" in section.attributes
            for section in abstract_sections
        )

        if has_labels:
            # Structured: extract only Results and Conclusions
            target_labels = {"RESULTS", "CONCLUSIONS", "CONCLUSION", "FINDINGS"}
            parts = []
            for section in abstract_sections:
                if hasattr(section, "attributes") and "Label" in section.attributes:
                    label = section.attributes["Label"]
                    if label.upper() in target_labels:
                        parts.append(f"{label}: {str(section)}")
            # If somehow no target sections matched, fall back to full abstract
            if not parts:
                return " ".join(str(s) for s in abstract_sections)
            return " ".join(parts)

        # Unstructured: return full text
        return " ".join(str(section) for section in abstract_sections)

    def _identify_study_type(self, title: str, abstract: str) -> str:
        """Identify study type from title and abstract.

        Args:
            title: Study title
            abstract: Study abstract

        Returns:
            Study type string
        """
        combined = (title + " " + abstract).lower()

        # Check for meta-analysis (highest quality)
        if re.search(r"meta-analysis|meta analysis|systematic review", combined):
            return "meta-analysis"

        # Check for RCT
        if re.search(r"randomized controlled trial|randomized control trial|rct|randomised", combined):
            return "rct"

        # Check for cohort study
        if re.search(r"cohort study|prospective study|longitudinal", combined):
            return "cohort study"

        # Check for case-control
        if re.search(r"case-control|case control", combined):
            return "case-control"

        # Check for review
        if re.search(r"review|literature review", combined):
            return "review"

        # Default to observational
        return "observational"

    def _extract_sample_size(self, abstract: str) -> int:
        """Extract sample size from abstract.

        Args:
            abstract: Study abstract

        Returns:
            Estimated sample size as integer
        """
        # Look for patterns like "n=150", "N = 200", "n=1,500"
        patterns = [
            r"n\s*=\s*(\d+,?\d*)",
            r"N\s*=\s*(\d+,?\d*)",
            r"(\d+,?\d*)\s+participants",
            r"(\d+,?\d*)\s+subjects",
            r"(\d+,?\d*)\s+patients"
        ]

        for pattern in patterns:
            match = re.search(pattern, abstract, re.IGNORECASE)
            if match:
                # Extract number and remove commas
                num_str = match.group(1).replace(",", "")
                try:
                    return int(num_str)
                except ValueError:
                    pass

        # Default if not found
        return 0

    async def search_and_fetch(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Study]:
        """Convenience method: search and fetch in one call.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of Study objects with full metadata
        """
        pubmed_ids = await self.search(query, max_results)
        if not pubmed_ids:
            return []

        return await self.fetch_details(pubmed_ids)
