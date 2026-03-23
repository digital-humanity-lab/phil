#' Validate a PhilCorpus object
#'
#' Checks internal consistency of a PhilCorpus: dimension agreement
#' between layers, segment data, and text metadata.
#'
#' @param x A PhilCorpus object.
#' @param strict If TRUE, stop on first error. If FALSE, return all issues.
#' @return Invisibly returns TRUE if valid, or a character vector of issues.
#' @export
validate_phil_corpus <- function(x, strict = TRUE) {
  issues <- character()

  if (!inherits(x, "PhilCorpus")) {
    issues <- c(issues, "Object is not a PhilCorpus")
    if (strict) stop(issues)
    return(issues)
  }

  n_seg <- n_segments(x)
  n_txt <- n_texts(x)

  # Check layer dimensions

  for (nm in names(x$layers)) {
    l <- x$layers[[nm]]
    if (is.matrix(l)) {
      if (nrow(l) != n_seg && n_seg > 0) {
        issues <- c(issues, sprintf(
          "Layer '%s' has %d rows but segmentData has %d rows", nm, nrow(l), n_seg))
      }
    }
  }

  # Check required segmentData columns
  if (n_seg > 0) {
    required_seg <- c("segment_id", "text_id")
    missing_seg <- setdiff(required_seg, names(x$segmentData))
    if (length(missing_seg) > 0) {
      issues <- c(issues, sprintf(
        "segmentData missing columns: %s", paste(missing_seg, collapse = ", ")))
    }
  }

  # Check required textMetadata columns
  if (n_txt > 0) {
    required_txt <- c("text_id")
    missing_txt <- setdiff(required_txt, names(x$textMetadata))
    if (length(missing_txt) > 0) {
      issues <- c(issues, sprintf(
        "textMetadata missing columns: %s", paste(missing_txt, collapse = ", ")))
    }
  }

  # Check conceptSpans
  if (!is.null(x$conceptSpans) && !inherits(x$conceptSpans, "ConceptSpans")) {
    issues <- c(issues, "conceptSpans must be a ConceptSpans object or NULL")
  }

  if (length(issues) > 0) {
    if (strict) stop(paste(issues, collapse = "\n"))
    return(issues)
  }

  invisible(TRUE)
}
