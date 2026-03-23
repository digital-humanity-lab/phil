#' Connect to the philosophical concepts database
#'
#' @param db_path Path to SQLite database. If NULL, uses bundled database.
#' @return A phil_concepts_db connection object.
#' @export
phil_concepts_db <- function(db_path = NULL) {
  if (is.null(db_path)) {
    db_path <- system.file("extdata", "phil_concepts.sqlite",
                           package = "phil.concepts.db")
    if (db_path == "") {
      stop("Bundled database not found. Run build_concepts_db() first.")
    }
  }
  con <- DBI::dbConnect(RSQLite::SQLite(), db_path)
  structure(list(con = con, path = db_path), class = "phil_concepts_db")
}

#' Select from concepts database (AnnotationDbi-style)
#'
#' @param db A phil_concepts_db object.
#' @param keys Character vector of keys to look up.
#' @param keytype Column to match keys against.
#' @param columns Columns to return.
#' @return data.frame of results.
#' @export
select.phil_concepts_db <- function(db, keys, keytype = "CONCEPT_ID", columns = NULL) {
  if (is.null(columns)) columns <- columns(db)

  cols_sql <- paste(columns, collapse = ", ")
  placeholders <- paste(rep("?", length(keys)), collapse = ", ")
  query <- sprintf("SELECT %s FROM concepts WHERE %s IN (%s)",
                   cols_sql, keytype, placeholders)

  DBI::dbGetQuery(db$con, query, params = list(keys))
}

#' List available key types
#' @param db A phil_concepts_db object.
#' @return Character vector.
#' @export
keytypes <- function(db) {
  c("CONCEPT_ID", "LABEL_EN", "LABEL_JA", "LABEL_DE", "LABEL_ZH",
    "TRADITION", "WIKIDATA_QID", "INPHO_ID")
}

#' List available columns
#' @param db A phil_concepts_db object.
#' @return Character vector.
#' @export
columns <- function(db) {
  c("CONCEPT_ID", "LABEL_EN", "LABEL_JA", "LABEL_DE", "LABEL_ZH", "LABEL_SA",
    "DEFINITION_EN", "TRADITION", "ERA", "RELATED_CONCEPTS",
    "WIKIDATA_QID", "INPHO_ID")
}

#' List keys for a given key type
#' @param db A phil_concepts_db object.
#' @param keytype Key type to list.
#' @return Character vector of keys.
#' @export
keys <- function(db, keytype = "CONCEPT_ID") {
  query <- sprintf("SELECT DISTINCT %s FROM concepts WHERE %s IS NOT NULL", keytype, keytype)
  result <- DBI::dbGetQuery(db$con, query)
  result[[1]]
}
