#' Compare philosophical concepts (workbench facade)
#'
#' High-level facade that delegates to philmap::phil_compare() or
#' philmap::phil_align() depending on arguments.
#'
#' @param a First concept (ID, label, or PhilCorpus).
#' @param b Second concept (ID, label, or PhilCorpus).
#' @param ... Additional arguments passed to philmap::phil_compare().
#' @return A phil_comparison object.
#' @export
phil_compare <- function(a, b, ...) {
  philmap::phil_compare(a, b, ...)
}
