#!/usr/bin/env python3
"""build_dbs.py - Build phil_concepts.sqlite and phil_traditions.sqlite.

Author: Yusuke Matsui
"""

import os
import sqlite3
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── helpers ──────────────────────────────────────────────────────────────────

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_era(era_str: str):
    """Parse era string like '-427 ~ -347' into (start, end) integers."""
    if not era_str or era_str == "-":
        return None, None
    parts = era_str.replace("~", "~").split("~")
    start_s = parts[0].strip().replace("present", "2026")
    end_s = parts[1].strip().replace("present", "2026") if len(parts) > 1 else start_s
    try:
        return int(start_s), int(end_s)
    except ValueError:
        return None, None


# ── 1. Build phil_concepts.sqlite ────────────────────────────────────────────

def build_concepts_db() -> None:
    out_dir = ROOT / "r" / "phil.concepts.db" / "inst" / "extdata"
    _ensure_dir(out_dir)
    db_path = out_dir / "phil_concepts.sqlite"

    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE concepts (
            CONCEPT_ID       TEXT PRIMARY KEY,
            LABEL_EN         TEXT,
            LABEL_JA         TEXT,
            LABEL_DE         TEXT,
            LABEL_ZH         TEXT,
            LABEL_SA         TEXT,
            DEFINITION_EN    TEXT,
            TRADITION        TEXT,
            ERA              TEXT,
            RELATED_CONCEPTS TEXT,
            WIKIDATA_QID     TEXT,
            INPHO_ID         TEXT
        );
    """)

    # fmt: off
    concepts = [
        ("phil:C00001", "autonomy",               "自律",     "Autonomie",    "自律",   None,                "Self-legislation of moral law",                                     "kantian_ethics",        "modern",            "phil:C00045,phil:C00078", "Q193891",  None),
        ("phil:C00003", "being/existence",         "存在",     "Sein",         "存在",   "sat",               "The most general concept in metaphysics",                           "ontology",              "ancient-present",   "phil:C00056",             "Q160151",  None),
        ("phil:C00012", "dao",                     "道",       None,           "道",     None,                "The Way; ultimate reality and natural order",                       "daoism",                "ancient",           "phil:C00178",             "Q178885",  None),
        ("phil:C00023", "ren (benevolence)",       "仁",       None,           "仁",     None,                "Humaneness; cardinal Confucian virtue",                             "confucianism",          "ancient",           "phil:C00156",             "Q847352",  None),
        ("phil:C00034", "sunyata (emptiness)",     "空",       None,           "空",     "śūnyatā",           "Emptiness; absence of inherent existence",                          "madhyamaka",            "ancient",           "phil:C00145,phil:C00167", "Q466649",  None),
        ("phil:C00045", "basho (place)",           "場所",     None,           None,     None,                "Nishida's concept of place/topos as ground of experience",          "kyoto_school",          "modern",            "phil:C00091",             None,       None),
        ("phil:C00056", "Dasein",                  "現存在",   "Dasein",       None,     None,                "Being-there; human existence as thrown into the world",             "phenomenology",         "modern",            "phil:C00089,phil:C00003", "Q582775",  None),
        ("phil:C00078", "karma",                   "業",       None,           "業",     "karma",             "Action and its consequences across lives",                          "hinduism",              "ancient",           "phil:C00190",             "Q131721",  None),
        ("phil:C00089", "Mitsein",                 "共存在",   "Mitsein",      None,     None,                "Being-with; structural feature of Dasein's existence",              "phenomenology",         "modern",            "phil:C00142,phil:C00056", None,       None),
        ("phil:C00091", "Lichtung",                "明るみ",   "Lichtung",     None,     None,                "Clearing; the open space where beings appear",                     "phenomenology",         "modern",            "phil:C00045",             None,       None),
        ("phil:C00101", "Aufhebung",               "止揚",     "Aufhebung",    None,     None,                "Sublation; simultaneous preservation, negation, and elevation",    "german_idealism",       "modern",            "phil:C00034",             "Q376544",  None),
        ("phil:C00112", "Ich-Du",                  "我と汝",   "Ich-Du",       None,     None,                "I-Thou relation; direct encounter with the Other",                 "dialogical_philosophy", "modern",            "phil:C00142",             None,       None),
        ("phil:C00123", "li (principle)",           "理",       None,           "理",     None,                "Principle; organizing pattern of reality",                         "neo_confucianism",      "medieval",          "phil:C00134",             None,       None),
        ("phil:C00134", "eidos",                   "エイドス", "Eidos",        None,     "eidos",             "Form; the essential nature of a thing",                            "platonism",             "ancient",           "phil:C00123",             "Q184876",  None),
        ("phil:C00142", "aidagara",                "間柄",     None,           None,     None,                "Betweenness; relational existence between persons",                "watsuji_ethics",        "modern",            "phil:C00089,phil:C00112,phil:C00156", None, None),
        ("phil:C00145", "pratityasamutpada",       "縁起",     None,           "缘起",   "pratītyasamutpāda", "Dependent origination; all phenomena arise in dependence",         "buddhism",              "ancient",           "phil:C00034,phil:C00156", "Q189746",  None),
        ("phil:C00156", "ubuntu",                  None,       None,           None,     None,                "A person is a person through other persons",                       "ubuntu_philosophy",     "modern",            "phil:C00023,phil:C00142", "Q1373266", None),
        ("phil:C00167", "differance",              "差延",     "Différance",   None,     None,                "Derrida's neologism: differing and deferring of meaning",          "poststructuralism",     "contemporary",      "phil:C00034",             None,       None),
        ("phil:C00178", "logos",                   "ロゴス",   "Logos",        None,     "logos",             "Reason; rational principle governing the cosmos",                  "ancient_greek",         "ancient",           "phil:C00012",             "Q189748",  None),
        ("phil:C00189", "Gelassenheit",            "放下",     "Gelassenheit", None,     None,                "Releasement; letting-be; openness to mystery",                     "phenomenology",         "modern",            "phil:C00178",             None,       None),
        ("phil:C00190", "inga (causality)",        "因果",     None,           "因果",   None,                "Cause and effect in Buddhist metaphysics",                         "buddhism_ea",           "ancient",           "phil:C00078",             None,       None),
    ]
    # fmt: on

    cur.executemany(
        "INSERT INTO concepts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        concepts,
    )

    cur.execute("CREATE INDEX idx_concepts_label_en ON concepts(LABEL_EN);")
    cur.execute("CREATE INDEX idx_concepts_label_ja ON concepts(LABEL_JA);")
    cur.execute("CREATE INDEX idx_concepts_tradition ON concepts(TRADITION);")

    con.commit()
    con.close()
    print(f"Built {db_path}  ({len(concepts)} concepts)")


# ── 2. Build phil_traditions.sqlite ──────────────────────────────────────────

def build_traditions_db() -> None:
    out_dir = ROOT / "r" / "phil.traditions.db" / "inst" / "extdata"
    _ensure_dir(out_dir)
    db_path = out_dir / "phil_traditions.sqlite"

    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE traditions (
            TRADITION_ID TEXT PRIMARY KEY,
            NAME_EN      TEXT,
            NAME_JA      TEXT,
            PARENT       TEXT,
            ERA_START    INTEGER,
            ERA_END      INTEGER,
            REGION       TEXT,
            DESCRIPTION  TEXT
        );
    """)

    # Load YAML sources
    traditions_yaml = ROOT / "shared" / "config" / "traditions.yaml"
    taxonomy_yaml = ROOT / "shared" / "data" / "school_taxonomy.yaml"

    with open(traditions_yaml) as f:
        traditions_cfg = yaml.safe_load(f)

    with open(taxonomy_yaml) as f:
        taxonomy = yaml.safe_load(f)

    rows = []

    # Top-level tradition labels from traditions.yaml
    top_labels = {
        "western":    ("Western Philosophy",    "西洋哲学"),
        "east_asian": ("East Asian Philosophy",  "東洋哲学"),
        "south_asian":("South Asian Philosophy", "南アジア哲学"),
        "islamic":    ("Islamic Philosophy",     "イスラム哲学"),
        "african":    ("African Philosophy",     "アフリカ哲学"),
    }

    for top_id, (name_en, name_ja) in top_labels.items():
        rows.append((top_id, name_en, name_ja, None, None, None, None,
                      f"Top-level tradition: {name_en}"))

    # Sub-level groupings from taxonomy (e.g. western > ancient, medieval, ...)
    sub_labels = {
        # western
        ("western", "ancient"):       ("Ancient Western",       "古代西洋哲学",    "greece_rome"),
        ("western", "medieval"):      ("Medieval Western",      "中世西洋哲学",    "europe"),
        ("western", "modern"):        ("Modern Western",        "近代西洋哲学",    "europe"),
        ("western", "contemporary"):  ("Contemporary Western",  "現代西洋哲学",    "global"),
        # east_asian
        ("east_asian", "chinese"):    ("Chinese Philosophy",    "中国哲学",        "china"),
        ("east_asian", "japanese"):   ("Japanese Philosophy",   "日本哲学",        "japan"),
        ("east_asian", "korean"):     ("Korean Philosophy",     "韓国哲学",        "korea"),
        # south_asian
        ("south_asian", "hindu"):     ("Hindu Philosophy",      "ヒンドゥー哲学",   "india"),
        ("south_asian", "buddhist"):  ("Buddhist Philosophy",   "仏教哲学",        "india"),
        ("south_asian", "heterodox"): ("Heterodox Indian",      "非正統派",        "india"),
        # islamic
        ("islamic", "kalam"):         ("Kalam",                 "カラーム",        "islamic_world"),
        ("islamic", "falsafa"):       ("Falsafa",               "ファルサファ",    "islamic_world"),
        ("islamic", "illuminationist"):("Illuminationist",      "照明学派",        "persia"),
    }

    for (parent, sub_id), (name_en, name_ja, region) in sub_labels.items():
        rows.append((sub_id, name_en, name_ja, parent, None, None, region,
                      f"Sub-tradition of {parent}"))

    # Leaf-level schools from taxonomy YAML
    for top_id, sub_groups in taxonomy.items():
        if isinstance(sub_groups, list):
            # african is a flat list
            for school in sub_groups:
                era_start, era_end = _parse_era(school.get("era", ""))
                rows.append((
                    school["id"],
                    school["name_en"],
                    school.get("name_ja"),
                    top_id,
                    era_start, era_end,
                    school.get("region"),
                    f"School within {top_id}",
                ))
        elif isinstance(sub_groups, dict):
            for sub_id, schools in sub_groups.items():
                if not isinstance(schools, list):
                    continue
                for school in schools:
                    era_start, era_end = _parse_era(school.get("era", ""))
                    rows.append((
                        school["id"],
                        school["name_en"],
                        school.get("name_ja"),
                        sub_id,
                        era_start, era_end,
                        school.get("region"),
                        f"School within {sub_id}",
                    ))

    cur.executemany(
        "INSERT OR IGNORE INTO traditions VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )

    cur.execute("CREATE INDEX idx_traditions_name_en ON traditions(NAME_EN);")
    cur.execute("CREATE INDEX idx_traditions_parent ON traditions(PARENT);")

    con.commit()
    con.close()
    print(f"Built {db_path}  ({len(rows)} traditions)")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_concepts_db()
    build_traditions_db()
    print("Done.")
