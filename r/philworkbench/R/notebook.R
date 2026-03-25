#' Inline citation for Quarto/RMarkdown
#'
#' Returns a formatted inline citation string for use in Quarto documents.
#'
#' @param results A phil_search_results or phil_exploration object.
#' @param rank Which result to cite (1 = top result).
#' @return Character string suitable for inline use.
#' @export
phil_inline_cite <- function(results, rank = 1) {
  if (inherits(results, "phil_exploration")) {
    df <- results$results
  } else if (inherits(results, "phil_search_results")) {
    df <- results$results
  } else {
    stop("Unsupported object type for inline citation")
  }

  if (nrow(df) < rank) {
    return("(no result)")
  }

  r <- df[rank, ]
  sprintf("%s (sim = %.2f, %s)", r$label, r$similarity, r$tradition)
}

#' Session information for reproducibility
#'
#' @return A list with Phil ecosystem version info and session details.
#' @export
phil_session_info <- function() {
  pkgs <- c("philcore", "philengine", "philmap", "philworkbench")
  versions <- vapply(pkgs, function(p) {
    tryCatch(as.character(utils::packageVersion(p)), error = function(e) "not installed")
  }, character(1))

  list(
    packages = setNames(versions, pkgs),
    r_version = R.version.string,
    platform = .Platform$OS.type,
    timestamp = Sys.time(),
    locale = Sys.getlocale()
  )
}
