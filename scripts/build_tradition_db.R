#!/usr/bin/env Rscript
# build_tradition_db.R — Create a SQLite database of philosophical traditions.
#
# Reads shared/config/traditions.yaml and inserts all traditions and
# sub-traditions into an SQLite database at:
#   r/phil.traditions.db/inst/extdata/phil_traditions.sqlite

library(DBI)
library(RSQLite)
library(yaml)

root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))

# ── Read traditions YAML ─────────────────────────────────────────────────────

yaml_path <- file.path(root, "shared", "config", "traditions.yaml")
if (!file.exists(yaml_path)) {
  stop("traditions.yaml not found at: ", yaml_path)
}
traditions_data <- yaml::yaml.load_file(yaml_path)
message("Loaded traditions.yaml")

# ── Output path ──────────────────────────────────────────────────────────────

out_dir <- file.path(root, "r", "phil.traditions.db", "inst", "extdata")
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
db_path <- file.path(out_dir, "phil_traditions.sqlite")

if (file.exists(db_path)) file.remove(db_path)

# ── Create database ─────────────────────────────────────────────────────────

con <- dbConnect(SQLite(), db_path)

dbExecute(con, "
CREATE TABLE traditions (
  id              TEXT PRIMARY KEY,
  label           TEXT NOT NULL,
  parent_id       TEXT,
  level           TEXT NOT NULL CHECK(level IN ('tradition', 'sub_tradition')),
  created_at      TEXT DEFAULT (datetime('now'))
);
")

# ── Parse and insert ─────────────────────────────────────────────────────────

rows <- list()

for (trad_id in names(traditions_data$traditions)) {
  trad <- traditions_data$traditions[[trad_id]]
  label <- trad$label

  # Insert the top-level tradition
  rows[[length(rows) + 1]] <- data.frame(
    id        = trad_id,
    label     = label,
    parent_id = NA_character_,
    level     = "tradition",
    stringsAsFactors = FALSE
  )

  # Insert each sub-tradition
  for (sub_id in trad$sub_traditions) {
    # Create a human-readable label from the sub-tradition id
    sub_label <- gsub("_", " ", sub_id)
    sub_label <- paste0(toupper(substring(sub_label, 1, 1)), substring(sub_label, 2))

    rows[[length(rows) + 1]] <- data.frame(
      id        = sub_id,
      label     = sub_label,
      parent_id = trad_id,
      level     = "sub_tradition",
      stringsAsFactors = FALSE
    )
  }
}

all_rows <- do.call(rbind, rows)
dbWriteTable(con, "traditions", all_rows, append = TRUE, row.names = FALSE)

message(sprintf(
  "Inserted %d rows (%d traditions, %d sub-traditions) into %s",
  nrow(all_rows),
  sum(all_rows$level == "tradition"),
  sum(all_rows$level == "sub_tradition"),
  db_path
))

# ── Create indices ───────────────────────────────────────────────────────────

dbExecute(con, "CREATE INDEX idx_traditions_parent ON traditions(parent_id);")
dbExecute(con, "CREATE INDEX idx_traditions_level ON traditions(level);")

dbDisconnect(con)
message("Done: ", db_path)
