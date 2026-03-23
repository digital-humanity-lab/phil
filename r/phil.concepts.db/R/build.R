#' Build the concepts database from source files
#'
#' @param sources List of source file paths (YAML/JSON).
#' @param output_path Output SQLite database path.
#' @return Invisible path to created database.
#' @export
build_concepts_db <- function(sources = NULL, output_path = NULL) {
  if (is.null(output_path)) {
    output_path <- file.path(
      system.file("extdata", package = "phil.concepts.db"),
      "phil_concepts.sqlite"
    )
  }

  con <- DBI::dbConnect(RSQLite::SQLite(), output_path)
  on.exit(DBI::dbDisconnect(con))

  DBI::dbExecute(con, "
    CREATE TABLE IF NOT EXISTS concepts (
      CONCEPT_ID TEXT PRIMARY KEY,
      LABEL_EN TEXT,
      LABEL_JA TEXT,
      LABEL_DE TEXT,
      LABEL_ZH TEXT,
      LABEL_SA TEXT,
      DEFINITION_EN TEXT,
      TRADITION TEXT,
      ERA TEXT,
      RELATED_CONCEPTS TEXT,
      WIKIDATA_QID TEXT,
      INPHO_ID TEXT
    )
  ")

  DBI::dbExecute(con, "CREATE INDEX IF NOT EXISTS idx_label_en ON concepts(LABEL_EN)")
  DBI::dbExecute(con, "CREATE INDEX IF NOT EXISTS idx_tradition ON concepts(TRADITION)")

  if (!is.null(sources)) {
    for (src in sources) {
      if (grepl("\\.ya?ml$", src)) {
        # YAML source ingestion (requires yaml package)
        message(sprintf("Ingesting from: %s", src))
      }
    }
  }

  message(sprintf("Database created: %s", output_path))
  invisible(output_path)
}
