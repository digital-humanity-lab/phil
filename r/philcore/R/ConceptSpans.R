#' Create a ConceptSpans object
#'
#' A GRanges-like object for annotating concept occurrences in philosophical texts.
#' Backed by a data.frame with concept positions, identifiers, and interpretation info.
#'
#' @param text_id Character vector of text identifiers.
#' @param start Integer vector of start positions (character offset).
#' @param end Integer vector of end positions.
#' @param concept_id Character vector of concept identifiers (e.g., "phil:C00142").
#' @param confidence Numeric vector of confidence scores (0-1).
#' @param annotator Character vector identifying the annotator ("human:dreyfus" or "model:philmap-e5-v2").
#' @param interpretation_id Character vector of interpretation layer identifiers.
#' @return A ConceptSpans S3 object.
#' @export
ConceptSpans <- function(text_id = character(),
                         start = integer(),
                         end = integer(),
                         concept_id = character(),
                         confidence = numeric(),
                         annotator = character(),
                         interpretation_id = character()) {
  df <- data.frame(
    text_id = text_id,
    start = start,
    end = end,
    concept_id = concept_id,
    confidence = confidence,
    annotator = annotator,
    interpretation_id = interpretation_id,
    stringsAsFactors = FALSE
  )
  structure(df, class = c("ConceptSpans", "data.frame"))
}

#' @export
print.ConceptSpans <- function(x, ...) {
  n <- nrow(x)
  cat(sprintf("ConceptSpans: %d annotations\n", n))
  if (n > 0) {
    n_concepts <- length(unique(x$concept_id))
    n_texts <- length(unique(x$text_id))
    n_interp <- length(unique(x$interpretation_id[x$interpretation_id != ""]))
    cat(sprintf("  Unique concepts: %d\n", n_concepts))
    cat(sprintf("  Texts covered: %d\n", n_texts))
    if (n_interp > 0) cat(sprintf("  Interpretation layers: %d\n", n_interp))
    if (n <= 6) {
      print.data.frame(x, row.names = FALSE)
    } else {
      print.data.frame(utils::head(x, 3), row.names = FALSE)
      cat(sprintf("  ... and %d more\n", n - 3))
    }
  }
  invisible(x)
}

#' @export
`[.ConceptSpans` <- function(x, i, j, ...) {
  df <- as.data.frame(x)
  result <- if (missing(j)) df[i, , drop = FALSE] else df[i, j, drop = FALSE]
  if (!missing(j)) return(result)
  structure(result, class = c("ConceptSpans", "data.frame"))
}

#' Filter ConceptSpans by concept ID
#' @param spans A ConceptSpans object.
#' @param concept_id Concept ID(s) to filter by.
#' @return Filtered ConceptSpans.
#' @export
filter_by_concept <- function(spans, concept_id) {
  stopifnot(inherits(spans, "ConceptSpans"))
  idx <- spans$concept_id %in% concept_id
  spans[idx, ]
}

#' Filter ConceptSpans by interpretation
#' @param spans A ConceptSpans object.
#' @param interpretation_id Interpretation ID(s) to filter by.
#' @return Filtered ConceptSpans.
#' @export
filter_by_interpretation <- function(spans, interpretation_id) {
  stopifnot(inherits(spans, "ConceptSpans"))
  idx <- spans$interpretation_id %in% interpretation_id
  spans[idx, ]
}
