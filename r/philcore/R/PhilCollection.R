#' Create a PhilCollection object
#'
#' A MultiAssayExperiment-like container holding multiple PhilCorpus objects
#' for cross-corpus analysis.
#'
#' @param ... Named PhilCorpus objects.
#' @return A PhilCollection S3 object.
#' @export
PhilCollection <- function(...) {
  corpora_list <- list(...)
  if (length(corpora_list) == 1 && is.list(corpora_list[[1]]) &&
      !inherits(corpora_list[[1]], "PhilCorpus")) {
    corpora_list <- corpora_list[[1]]
  }
  for (nm in names(corpora_list)) {
    if (!inherits(corpora_list[[nm]], "PhilCorpus")) {
      stop(sprintf("Element '%s' is not a PhilCorpus object", nm))
    }
  }
  structure(corpora_list, class = "PhilCollection")
}

#' @export
print.PhilCollection <- function(x, ...) {
  cat(sprintf("PhilCollection: %d corpora\n", length(x)))
  for (nm in names(x)) {
    corpus <- x[[nm]]
    cat(sprintf("  %s: %d segments, %d texts\n",
                nm, n_segments(corpus), n_texts(corpus)))
  }
  invisible(x)
}

#' Access corpora from a PhilCollection
#' @param x A PhilCollection object.
#' @return Named list of PhilCorpus objects.
#' @export
corpora <- function(x) {
  stopifnot(inherits(x, "PhilCollection"))
  unclass(x)
}
