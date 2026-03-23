# Phil Data Directory

This directory holds philosophical text corpora and knowledge graph data used by the Phil ecosystem packages.

## Directory Structure

```
data/
├── oa_philosophy/       # Open access philosophy papers (fetched via philcorpus)
│   └── philpapers/      # PhilPapers records imported from digital-philosophy-ecosystem
├── classical_texts/     # Classical philosophical texts
│   ├── gutenberg/       # Project Gutenberg philosophy texts (English)
│   └── ctp/             # Chinese Text Project texts (Classical Chinese)
└── knowledge_graph/     # Philosopher/concept graph data (philgraph-compatible)
    └── wikidata_graph.json
```

## Data Sources

| Source | Script | Format |
|--------|--------|--------|
| OpenAlex, J-STAGE, PhilArchive | `scripts/fetch_oa_philosophy.py` | PhilCorpus JSON |
| Wikidata, Gutenberg, CTP, PhilPapers | `scripts/import_existing_data.py` | PhilCorpus / PhilGraph JSON |

## Usage

Fetch new OA papers:

```bash
python scripts/fetch_oa_philosophy.py --source openalex --limit 100 --output data/oa_philosophy/
python scripts/fetch_oa_philosophy.py --source jstage --limit 50 --language ja --output data/oa_philosophy/
```

Import existing data from digital-philosophy-ecosystem:

```bash
python scripts/import_existing_data.py --all
python scripts/import_existing_data.py --source gutenberg
```

## Notes

- Large data files are not committed to the repository. Use the scripts above to populate this directory.
- All fetched data respects original licensing. See each document's `license` field.
