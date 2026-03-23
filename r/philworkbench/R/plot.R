#' Plot Phil ecosystem objects
#'
#' Generic plotting function that dispatches based on object type.
#'
#' @param x A Phil ecosystem object (PhilCorpus, phil_comparison, phil_exploration, etc.)
#' @param type Plot type. Available types depend on object class.
#' @param ... Additional arguments passed to specific plot methods.
#' @return A plot (ggplot2 or base).
#' @export
phil_plot <- function(x, type = NULL, ...) {
  UseMethod("phil_plot")
}

#' @export
phil_plot.PhilCorpus <- function(x, type = "overview", ...) {
  plot.PhilCorpus(x, type = type, ...)
}

#' @export
phil_plot.phil_comparison <- function(x, type = "bar", ...) {
  plot.phil_comparison(x, type = type, ...)
}

#' @export
phil_plot.phil_exploration <- function(x, type = "tradition_map", ...) {
  plot.phil_exploration(x, type = type, ...)
}

#' @export
phil_plot.phil_search_results <- function(x, type = "tradition_map", ...) {
  plot.phil_search_results(x, type = type, ...)
}

#' @export
phil_plot.phil_genealogy <- function(x, type = "network", ...) {
  plot.phil_genealogy(x, ...)
}

#' @export
phil_plot.default <- function(x, type = NULL, ...) {
  message(sprintf("No phil_plot method for class: %s", paste(class(x), collapse = ", ")))
  invisible(x)
}
