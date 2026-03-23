#' Read a philosophical text into a PhilCorpus
#'
#' @param source Path, URL, or PhilCorpusHub identifier.
#' @param section Optional section filter.
#' @return A PhilCorpus object.
#' @export
phil_read <- function(source, section = NULL) {
  philcore::phil_load(source, section = section)
}

#' Segment a PhilCorpus into units
#'
#' @param corpus A PhilCorpus object.
#' @param type Segmentation type: "paragraph", "sentence", "argument".
#' @return Updated PhilCorpus with segmentation.
#' @export
phil_segment <- function(corpus, type = "paragraph") {
  stopifnot(inherits(corpus, "PhilCorpus"))
  type <- match.arg(type, c("paragraph", "sentence", "argument"))
  # Segmentation logic depends on text content
  message(sprintf("Segmenting by %s (implementation pending)", type))
  corpus
}

#' Look up a concept, thinker, or text
#'
#' @param query Search query string.
#' @param type Type to search: "concept", "thinker", "text", "all".
#' @return data.frame of results.
#' @export
phil_lookup <- function(query, type = "all") {
  type <- match.arg(type, c("all", "concept", "thinker", "text"))
  # Query phil.concepts.db if available
  if (requireNamespace("phil.concepts.db", quietly = TRUE)) {
    phil.concepts.db::phil_concept_search(query)
  } else {
    message("phil.concepts.db not installed. Install for concept lookup.")
    data.frame()
  }
}
