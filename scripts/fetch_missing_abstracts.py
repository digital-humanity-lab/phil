"""Fetch abstracts for papers missing them from Crossref and Semantic Scholar."""
import httpx
import json
import re
import time
import sys
from pathlib import Path

DATA_PATH = Path("data/journal_abstracts/top_journals_abstracts.json")

def clean_abstract(text: str) -> str:
    """Remove XML/HTML tags and clean up abstract text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = text.strip()
    return text

def get_doi_from_openalex(oa_id: str, client: httpx.Client) -> str | None:
    """Look up DOI from OpenAlex API."""
    work_id = oa_id.replace("https://openalex.org/", "")
    try:
        resp = client.get(
            f"https://api.openalex.org/works/{work_id}",
            params={"select": "doi"},
            timeout=15
        )
        if resp.status_code == 200:
            doi = resp.json().get("doi", "")
            if doi:
                return doi.replace("https://doi.org/", "")
    except Exception as e:
        print(f"  OpenAlex error for {work_id}: {e}")
    return None

def try_crossref(doi: str, client: httpx.Client) -> str | None:
    """Try to get abstract from Crossref."""
    headers = {"User-Agent": "PhilEcosystem/0.1 (mailto:mail.to.matsui@gmail.com)"}
    try:
        resp = client.get(
            f"https://api.crossref.org/works/{doi}",
            headers=headers,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json().get("message", {})
            abstract = data.get("abstract", "")
            if abstract and len(abstract) > 50:
                return clean_abstract(abstract)
    except Exception as e:
        print(f"  Crossref error for {doi}: {e}")
    return None

def try_semantic_scholar(doi: str, client: httpx.Client) -> str | None:
    """Try to get abstract from Semantic Scholar."""
    try:
        resp = client.get(
            f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
            params={"fields": "abstract"},
            headers={"User-Agent": "PhilEcosystem/0.1"},
            timeout=15
        )
        if resp.status_code == 200:
            abstract = resp.json().get("abstract", "")
            if abstract and len(abstract) > 50:
                return abstract
    except Exception as e:
        print(f"  S2 error for {doi}: {e}")
    return None

def main():
    papers = json.loads(DATA_PATH.read_text())
    need_abstract = [p for p in papers if not p.get("abstract") or len(p.get("abstract", "")) < 100]

    print(f"Total papers: {len(papers)}")
    print(f"Papers needing abstracts: {len(need_abstract)}")

    found_crossref = 0
    found_s2 = 0
    no_doi = 0

    with httpx.Client() as client:
        for i, paper in enumerate(need_abstract):
            title = paper.get("title", "Unknown")[:60]
            oa_id = paper.get("id", "")
            print(f"\n[{i+1}/{len(need_abstract)}] {title}")

            # Step 1: Get DOI from OpenAlex
            doi = get_doi_from_openalex(oa_id, client)
            if not doi:
                print(f"  No DOI found")
                no_doi += 1
                time.sleep(0.2)
                continue

            print(f"  DOI: {doi}")
            time.sleep(0.2)  # polite delay after OpenAlex

            # Step 2: Try Crossref
            abstract = try_crossref(doi, client)
            if abstract:
                paper["abstract"] = abstract
                paper["abstract_source"] = "crossref"
                found_crossref += 1
                print(f"  -> Crossref abstract ({len(abstract)} chars)")
                time.sleep(0.5)
                continue

            time.sleep(0.5)

            # Step 3: Try Semantic Scholar
            abstract = try_semantic_scholar(doi, client)
            if abstract:
                paper["abstract"] = abstract
                paper["abstract_source"] = "semantic_scholar"
                found_s2 += 1
                print(f"  -> S2 abstract ({len(abstract)} chars)")
                time.sleep(3)  # S2 stricter rate limit
                continue

            time.sleep(3)
            print(f"  No abstract found")

    print(f"\n=== Results ===")
    print(f"Found from Crossref: {found_crossref}")
    print(f"Found from Semantic Scholar: {found_s2}")
    print(f"No DOI available: {no_doi}")
    print(f"Still missing: {len(need_abstract) - found_crossref - found_s2 - no_doi}")

    # Save enriched data
    DATA_PATH.write_text(json.dumps(papers, indent=2, ensure_ascii=False))
    print(f"\nSaved to {DATA_PATH}")

    # Verify
    remaining = [p for p in papers if not p.get("abstract") or len(p.get("abstract", "")) < 100]
    print(f"Papers still needing abstracts: {len(remaining)}")

if __name__ == "__main__":
    main()
