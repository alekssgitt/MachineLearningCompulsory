import json
import re
import ssl
import urllib.parse
import urllib.request
from datetime import date

import certifi

source = "OpenAlex field cited_by_count"
citation_words = {
    "at least": "at_least",
    "more than": "more_than",
    "fewer than": "fewer_than",
    "at most": "at_most",
    "about": "about",
}


def read_constraints(text: str) -> tuple[str, int | None, str, int | None]:
    lower = text.lower()
    year_relation, year = "any", None
    year_match = re.search(r"\b(before|after|since)\s+(\d{4})\b", lower)
    published_in = re.search(r"\bpublished in\s+(\d{4})\b", lower)
    if year_match:
        year_relation, year = year_match.group(1), int(year_match.group(2))
    elif published_in:
        year_relation, year = "in", int(published_in.group(1))
    elif "recent" in lower:
        year_relation, year = "since", date.today().year - 2

    citation_relation, citation_count = "any", None
    citation_match = re.search(r"\b(at least|more than|fewer than|at most|about)\s+(\d+)\b", lower)
    if citation_match:
        citation_relation = citation_words[citation_match.group(1)]
        citation_count = int(citation_match.group(2))
    return year_relation, year, citation_relation, citation_count

_SEARCH = "https://api.openalex.org/works"


def _abstract(index: dict | None) -> str:
    if not index:
        return ""
    size = max(pos for positions in index.values() for pos in positions) + 1
    words = [""] * size
    for word, positions in index.items():
        for pos in positions:
            if 0 <= pos < size:
                words[pos] = word
    return " ".join(word for word in words if word)[:500]


def fetch_papers(topic: str, limit: int = 8) -> list[dict]:
    query = urllib.parse.urlencode({
        "search": topic,
        "per-page": limit,
        "select": "display_name,publication_year,authorships,cited_by_count,doi,id,abstract_inverted_index",
    })
    request = urllib.request.Request(
        f"{_SEARCH}?{query}",
        headers={"User-Agent": "ResearchScout/1.0", "Accept": "application/json"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    papers = []
    for item in payload.get("results") or []:
        title = item.get("display_name")
        url = item.get("doi") or item.get("id")
        if not title or not url:
            continue
        authors = [
            (authorship.get("author") or {}).get("display_name")
            for authorship in item.get("authorships") or []
        ]
        papers.append({
            "title": title,
            "authors": [name for name in authors if name],
            "year": item.get("publication_year"),
            "citation_count": item.get("cited_by_count"),
            "citation_source": source,
            "url": url,
            "abstract": _abstract(item.get("abstract_inverted_index")),
        })
    return papers


def rejection_reason(paper: dict, year_relation: str, year: int | None,
                     citation_relation: str, citation_count: int | None) -> str | None:
    paper_year = paper.get("year")
    if year_relation != "any":
        if year is None:
            return "no year value was given for the year constraint"
        if paper_year is None:
            return "publication year was missing"
        if year_relation == "before" and not paper_year < year:
            return f"published in {paper_year}, not before {year}"
        if year_relation == "after" and not paper_year > year:
            return f"published in {paper_year}, not after {year}"
        if year_relation == "in" and paper_year != year:
            return f"published in {paper_year}, not in {year}"
        if year_relation == "since" and paper_year < year:
            return f"published in {paper_year}, not in or after {year}"

    count = paper.get("citation_count")
    if citation_relation != "any":
        if citation_count is None:
            return "no citation value was given for the citation constraint"
        if count is None:
            return "citation count was missing from OpenAlex"
        if citation_relation == "at_least" and count < citation_count:
            return f"{count} citations, not at least {citation_count}"
        if citation_relation == "more_than" and count <= citation_count:
            return f"{count} citations, not more than {citation_count}"
        if citation_relation == "at_most" and count > citation_count:
            return f"{count} citations, not at most {citation_count}"
        if citation_relation == "fewer_than" and count >= citation_count:
            return f"{count} citations, not fewer than {citation_count}"
        if citation_relation == "about":
            low, high = int(citation_count * 0.75), int(citation_count * 1.25) + 1
            if not low <= count <= high:
                return f"{count} citations, not about {citation_count}"
    return None


def select_papers(papers: list[dict], year_relation: str = "any", year: int | None = None,
                  citation_relation: str = "any", citation_count: int | None = None) -> tuple[list[dict], list[dict]]:
    matches, rejected = [], []
    for paper in papers:
        reason = rejection_reason(paper, year_relation, year, citation_relation, citation_count)
        if reason:
            rejected.append({"title": paper["title"], "reason": reason})
        else:
            matches.append(paper)
    matches.sort(key=lambda paper: paper["citation_count"] or -1, reverse=True)
    return matches, rejected
