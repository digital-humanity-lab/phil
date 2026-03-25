#!/usr/bin/env python3
"""Fetch open access philosophy papers from multiple sources.

Usage:
    python scripts/fetch_oa_philosophy.py --source openalex --limit 100 --output data/oa_philosophy/
    python scripts/fetch_oa_philosophy.py --source jstage --limit 50 --output data/oa_japanese/
    python scripts/fetch_oa_philosophy.py --source all --limit 50 --output data/oa_all/
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Fetch OA philosophy papers")
    parser.add_argument(
        "--source",
        choices=[
            "openalex",
            "jstage",
            "philarchive",
            "cinii",
            "gutenberg",
            "ctp",
            "aozora",
            "all",
        ],
        default="openalex",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=str, default="data/oa_philosophy/")
    parser.add_argument(
        "--tradition", type=str, default=None, help="Filter by tradition"
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Filter by language (en, ja, de, fr)",
    )
    parser.add_argument("--year-from", type=int, default=2000)
    parser.add_argument("--year-to", type=int, default=2026)
    args = parser.parse_args()

    # Import and run pipeline
    from philcorpus.pipeline import CorpusPipeline

    pipeline = CorpusPipeline(output_dir=args.output)

    sources = (
        [args.source]
        if args.source != "all"
        else ["openalex", "jstage", "gutenberg", "ctp", "aozora"]
    )

    for source in sources:
        pipeline.add_source(
            source,
            limit=args.limit,
            tradition=args.tradition,
            language=args.language,
            year_from=args.year_from,
            year_to=args.year_to,
        )

    documents = pipeline.fetch_all()
    print(f"Fetched {len(documents)} documents")

    # Save raw documents
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    docs_data = [
        {
            "id": d.id,
            "title": d.title,
            "authors": d.authors,
            "year": d.year,
            "language": d.language,
            "tradition": d.tradition,
            "source": d.source,
            "url": d.url,
            "fulltext_url": d.fulltext_url,
            "license": d.license,
            "abstract": d.abstract,
            "has_fulltext": d.fulltext is not None,
        }
        for d in documents
    ]

    with open(output_path / "documents.json", "w", encoding="utf-8") as f:
        json.dump(docs_data, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path / 'documents.json'}")

    # Convert to PhilCorpus
    corpus = pipeline.to_philcorpus(documents)
    print(f"PhilCorpus: {corpus.n_concepts} concepts x {corpus.n_texts} texts")


if __name__ == "__main__":
    main()
