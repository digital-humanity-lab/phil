#!/usr/bin/env python3
"""Import existing data from digital-philosophy-ecosystem into Phil format.

Usage:
    python scripts/import_existing_data.py --all
    python scripts/import_existing_data.py --source wikidata
    python scripts/import_existing_data.py --source gutenberg --output data/classical_texts/
"""
import argparse
import json
from pathlib import Path

ECOSYSTEM_DATA = Path("/home/matsui/github/digital-philosophy-ecosystem/data")
OUTPUT_DIR = Path("/home/matsui/github/phil/data")


def import_wikidata():
    """Import Wikidata philosophers and influences into philgraph-compatible format."""
    out_dir = OUTPUT_DIR / "knowledge_graph"
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes = []
    edges = []

    # Import philosophers
    philosophers_file = ECOSYSTEM_DATA / "wikidata" / "philosophers.json"
    if philosophers_file.exists():
        with open(philosophers_file, encoding="utf-8") as f:
            philosophers = json.load(f)

        for p in philosophers:
            nodes.append(
                {
                    "id": p.get("id", ""),
                    "label": p.get("name", p.get("label", "")),
                    "type": "philosopher",
                    "birth_year": p.get("birth_year"),
                    "death_year": p.get("death_year"),
                    "tradition": p.get("tradition", []),
                    "source": "wikidata",
                }
            )
        print(f"  Imported {len(nodes)} philosophers from Wikidata")
    else:
        print(f"  Warning: {philosophers_file} not found")

    # Import influences
    influences_file = ECOSYSTEM_DATA / "wikidata" / "influences.json"
    if influences_file.exists():
        with open(influences_file, encoding="utf-8") as f:
            influences = json.load(f)

        for inf in influences:
            edges.append(
                {
                    "source": inf.get("influencer", inf.get("source", "")),
                    "target": inf.get("influenced", inf.get("target", "")),
                    "type": "influenced_by",
                    "source_db": "wikidata",
                }
            )
        print(f"  Imported {len(edges)} influence relations")
    else:
        print(f"  Warning: {influences_file} not found")

    # Import movements
    movements_file = ECOSYSTEM_DATA / "wikidata" / "movements.json"
    if movements_file.exists():
        with open(movements_file, encoding="utf-8") as f:
            movements = json.load(f)

        for m in movements:
            nodes.append(
                {
                    "id": m.get("id", ""),
                    "label": m.get("name", m.get("label", "")),
                    "type": "movement",
                    "tradition": m.get("tradition", []),
                    "source": "wikidata",
                }
            )
        print(f"  Imported {len([n for n in nodes if n['type'] == 'movement'])} movements")
    else:
        print(f"  Warning: {movements_file} not found")

    # Write philgraph-compatible output
    graph_data = {"nodes": nodes, "edges": edges}
    output_file = out_dir / "wikidata_graph.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {output_file}")
    return graph_data


def import_gutenberg():
    """Import Gutenberg texts into PhilCorpus format."""
    out_dir = OUTPUT_DIR / "classical_texts" / "gutenberg"
    out_dir.mkdir(parents=True, exist_ok=True)

    gutenberg_dir = ECOSYSTEM_DATA / "gutenberg"
    if not gutenberg_dir.exists():
        print(f"  Warning: {gutenberg_dir} not found")
        return []

    documents = []
    for txt_file in sorted(gutenberg_dir.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8", errors="replace")

        # Extract title from filename
        title = txt_file.stem.replace("_", " ").replace("-", " ").title()

        doc = {
            "id": f"gutenberg:{txt_file.stem}",
            "title": title,
            "source": "gutenberg",
            "language": "en",
            "format": "plaintext",
            "filename": txt_file.name,
            "char_count": len(text),
            "line_count": text.count("\n"),
        }
        documents.append(doc)

        # Copy text to output
        out_file = out_dir / txt_file.name
        out_file.write_text(text, encoding="utf-8")

    # Write index
    index_file = out_dir / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"  Imported {len(documents)} Gutenberg texts")
    print(f"  Saved index to {index_file}")
    return documents


def import_ctp():
    """Import Chinese Text Project data into PhilCorpus format."""
    out_dir = OUTPUT_DIR / "classical_texts" / "ctp"
    out_dir.mkdir(parents=True, exist_ok=True)

    ctp_dir = ECOSYSTEM_DATA / "ctp"
    if not ctp_dir.exists():
        print(f"  Warning: {ctp_dir} not found")
        return []

    documents = []
    for json_file in sorted(ctp_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                doc = {
                    "id": f"ctp:{item.get('id', json_file.stem)}",
                    "title": item.get("title", json_file.stem),
                    "source": "ctp",
                    "language": "zh",
                    "tradition": "chinese",
                }
                documents.append(doc)
        elif isinstance(data, dict):
            doc = {
                "id": f"ctp:{data.get('id', json_file.stem)}",
                "title": data.get("title", json_file.stem),
                "source": "ctp",
                "language": "zh",
                "tradition": "chinese",
            }
            documents.append(doc)

    # Copy source files
    for json_file in ctp_dir.glob("*.json"):
        out_file = out_dir / json_file.name
        out_file.write_text(json_file.read_text(encoding="utf-8"), encoding="utf-8")

    # Write index
    index_file = out_dir / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"  Imported {len(documents)} CTP texts")
    print(f"  Saved index to {index_file}")
    return documents


def import_philpapers():
    """Import PhilPapers records into PhilCorpus format."""
    out_dir = OUTPUT_DIR / "oa_philosophy" / "philpapers"
    out_dir.mkdir(parents=True, exist_ok=True)

    philpapers_dir = ECOSYSTEM_DATA / "philpapers"
    if not philpapers_dir.exists():
        print(f"  Warning: {philpapers_dir} not found")
        return []

    documents = []
    for json_file in sorted(philpapers_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        records = data if isinstance(data, list) else [data]
        for record in records:
            doc = {
                "id": f"philpapers:{record.get('id', '')}",
                "title": record.get("title", ""),
                "authors": record.get("authors", []),
                "year": record.get("year"),
                "language": record.get("language", "en"),
                "source": "philpapers",
                "abstract": record.get("abstract", ""),
                "url": record.get("url", ""),
            }
            documents.append(doc)

    # Write index
    index_file = out_dir / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"  Imported {len(documents)} PhilPapers records")
    print(f"  Saved index to {index_file}")
    return documents


def main():
    parser = argparse.ArgumentParser(
        description="Import existing data into Phil format"
    )
    parser.add_argument(
        "--source",
        choices=["wikidata", "gutenberg", "ctp", "philpapers"],
        default=None,
        help="Specific source to import",
    )
    parser.add_argument(
        "--all", action="store_true", help="Import all available sources"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override output directory",
    )
    args = parser.parse_args()

    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output)

    if not ECOSYSTEM_DATA.exists():
        print(f"Error: Ecosystem data directory not found: {ECOSYSTEM_DATA}")
        print("Please clone digital-philosophy-ecosystem first.")
        return

    importers = {
        "wikidata": import_wikidata,
        "gutenberg": import_gutenberg,
        "ctp": import_ctp,
        "philpapers": import_philpapers,
    }

    if args.all:
        sources = list(importers.keys())
    elif args.source:
        sources = [args.source]
    else:
        parser.print_help()
        return

    for source in sources:
        print(f"\nImporting {source}...")
        importers[source]()

    print("\nDone.")


if __name__ == "__main__":
    main()
