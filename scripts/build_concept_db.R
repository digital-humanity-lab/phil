#!/usr/bin/env Rscript
# build_concept_db.R — Create a SQLite database of philosophical concepts.
#
# Reads shared/data/school_taxonomy.yaml for tradition context and inserts
# 10+ canonical cross-tradition concepts into an SQLite database at:
#   r/phil.concepts.db/inst/extdata/phil_concepts.sqlite

library(DBI)
library(RSQLite)
library(yaml)

root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))

# ── Read taxonomy for reference ──────────────────────────────────────────────

taxonomy_path <- file.path(root, "shared", "data", "school_taxonomy.yaml")
if (file.exists(taxonomy_path)) {
  taxonomy <- yaml::yaml.load_file(taxonomy_path)
  message("Loaded school_taxonomy.yaml")
} else {
  message("Warning: school_taxonomy.yaml not found, proceeding without it")
  taxonomy <- list()
}

# ── Output path ──────────────────────────────────────────────────────────────

out_dir <- file.path(root, "r", "phil.concepts.db", "inst", "extdata")
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
db_path <- file.path(out_dir, "phil_concepts.sqlite")

if (file.exists(db_path)) file.remove(db_path)

# ── Create database ─────────────────────────────────────────────────────────

con <- dbConnect(SQLite(), db_path)

dbExecute(con, "
CREATE TABLE concepts (
  id            TEXT PRIMARY KEY,
  label_primary TEXT NOT NULL,
  label_native  TEXT,
  lang          TEXT NOT NULL,
  tradition     TEXT NOT NULL,
  sub_tradition TEXT,
  domain        TEXT NOT NULL,
  definition_en TEXT,
  created_at    TEXT DEFAULT (datetime('now'))
);
")

# ── Insert sample concepts ───────────────────────────────────────────────────

concepts <- data.frame(
  id            = c("autonomy", "dasein", "aidagara", "ubuntu", "ren",
                    "sunyata", "basho", "aufhebung", "dao", "karma"),
  label_primary = c("autonomy", "Dasein", "aidagara", "ubuntu", "ren",
                    "sunyata", "basho", "Aufhebung", "dao", "karma"),
  label_native  = c("autonomy", "Dasein", "\u9593\u67c4", "ubuntu",
                    "\u4ec1", "\u7a7a", "\u5834\u6240",
                    "Aufhebung", "\u9053", "\u0915\u0930\u094d\u092e"),
  lang          = c("eng", "deu", "jpn", "zul", "zho",
                    "san", "jpn", "deu", "zho", "san"),
  tradition     = c("western", "western", "east_asian", "african",
                    "east_asian", "south_asian", "east_asian",
                    "western", "east_asian", "south_asian"),
  sub_tradition = c("early_modern_rationalist", "phenomenology",
                    "kyoto_school", "ubuntu",
                    "confucianism", "mahayana_buddhism",
                    "kyoto_school", "german_idealism",
                    "daoism", "theravada_buddhism"),
  domain        = c("ethics", "ontology", "ethics", "ethics", "ethics",
                    "metaphysics", "ontology", "metaphysics",
                    "metaphysics", "ethics"),
  definition_en = c(
    "Self-governance; the capacity of a rational agent to make decisions independently.",
    "Heidegger's term for the being that questions its own being; being-there.",
    "Watsuji Tetsuro's concept of betweenness in human relational existence.",
    "I am because we are; African relational ethics and communal personhood.",
    "Confucian benevolence / humaneness; the cardinal virtue of empathetic concern.",
    "Emptiness; the absence of inherent existence in all phenomena (Mahayana Buddhism).",
    "Nishida Kitaro's concept of place/topos as the ground of self-awareness.",
    "Hegel's sublation: simultaneous negation, preservation, and elevation.",
    "The Way; the fundamental principle of reality and proper conduct in Daoism.",
    "The law of moral causation; actions shape future experience across lifetimes."
  ),
  stringsAsFactors = FALSE
)

dbWriteTable(con, "concepts", concepts, append = TRUE, row.names = FALSE)

message(sprintf("Inserted %d concepts into %s", nrow(concepts), db_path))

# ── Create index ─────────────────────────────────────────────────────────────

dbExecute(con, "CREATE INDEX idx_concepts_tradition ON concepts(tradition);")
dbExecute(con, "CREATE INDEX idx_concepts_domain ON concepts(domain);")

dbDisconnect(con)
message("Done: ", db_path)
