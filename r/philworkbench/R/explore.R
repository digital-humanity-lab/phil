#' Explore philosophical concepts
#'
#' Free-text conceptual exploration across traditions and languages.
#' Combines concept search, cross-tradition mapping, and visualization.
#'
#' @param query Free-text query (e.g., "the relationship between self and other").
#' @param traditions Character vector of traditions to search, or NULL for all.
#' @param top_k Number of results.
#' @param engine A phil_engine object.
#' @return A phil_exploration S3 object.
#' @export
phil_explore <- function(query, traditions = NULL, top_k = 20, engine = NULL) {
  search_results <- philmap::phil_search(query, traditions = traditions,
                                          top_k = top_k, engine = engine)

  structure(
    list(
      query = query,
      traditions = traditions,
      results = search_results$results,
      model = search_results$model,
      timestamp = Sys.time()
    ),
    class = "phil_exploration"
  )
}

#' @export
print.phil_exploration <- function(x, ...) {
  cat("Phil Exploration\n")
  cat(sprintf("  Query: \"%s\"\n", x$query))
  n <- nrow(x$results)
  cat(sprintf("  Results: %d concepts across traditions\n", n))
  if (n > 0) {
    traditions <- unique(x$results$tradition)
    cat(sprintf("  Traditions: %s\n", paste(traditions, collapse = ", ")))
    cat("\n  Top matches:\n")
    top <- utils::head(x$results, 5)
    for (i in seq_len(nrow(top))) {
      r <- top[i, ]
      cat(sprintf("    %d. %s (%.3f) [%s]\n", i, r$label, r$similarity, r$tradition))
    }
  }
  invisible(x)
}

#' @export
plot.phil_exploration <- function(x, type = "tradition_map", ...) {
  if (nrow(x$results) == 0) {
    message("No results to plot")
    return(invisible(NULL))
  }
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("ggplot2 required")
  }

  df <- x$results

  if (type == "tradition_map") {
    ggplot2::ggplot(df, ggplot2::aes(x = reorder(.data$label, .data$similarity),
                                      y = .data$similarity,
                                      fill = .data$tradition)) +
      ggplot2::geom_col() +
      ggplot2::coord_flip() +
      ggplot2::labs(title = sprintf("Exploration: %s", x$query),
                    x = "", y = "Similarity") +
      ggplot2::theme_minimal()
  }
}
