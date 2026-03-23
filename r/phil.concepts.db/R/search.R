#' Search for concepts by text query
#'
#' @param query Search text.
#' @param language Language to search in: "en", "ja", "de", "zh".
#' @param db A phil_concepts_db object. If NULL, connects to default.
#' @return data.frame of matching concepts.
#' @export
phil_concept_search <- function(query, language = "en", db = NULL) {
  if (is.null(db)) db <- phil_concepts_db()

  col <- switch(language,
    en = "LABEL_EN",
    ja = "LABEL_JA",
    de = "LABEL_DE",
    zh = "LABEL_ZH",
    "LABEL_EN"
  )

  sql <- sprintf(
    "SELECT CONCEPT_ID, LABEL_EN, LABEL_JA, TRADITION, DEFINITION_EN
     FROM concepts WHERE %s LIKE ?", col)
  DBI::dbGetQuery(db$con, sql, params = list(paste0("%", query, "%")))
}

#' Get detailed info for a concept
#'
#' @param concept_id Concept identifier (e.g., "phil:C00142").
#' @param db A phil_concepts_db object.
#' @return Named list with concept details.
#' @export
phil_concept_info <- function(concept_id, db = NULL) {
  if (is.null(db)) db <- phil_concepts_db()

  result <- select.phil_concepts_db(db, keys = concept_id, keytype = "CONCEPT_ID")
  if (nrow(result) == 0) return(NULL)
  as.list(result[1, ])
}
