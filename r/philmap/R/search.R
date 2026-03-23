#' Search for similar philosophical concepts
#'
#' @param query Text query or concept identifier.
#' @param traditions Character vector of traditions to search within, or NULL for all.
#' @param top_k Number of results to return.
#' @param engine A phil_engine object.
#' @return A phil_search_results S3 object.
#' @export
phil_search <- function(query, traditions = NULL, top_k = 10, engine = NULL) {
  if (is.null(engine)) engine <- philengine::phil_engine()

  body <- list(query = query, top_k = top_k)
  if (!is.null(traditions)) body$traditions <- traditions

  resp <- tryCatch(
    .api_post(engine$api_url, "/search", body),
    error = function(e) {
      list(results = list(), query = query, model = engine$model, error = e$message)
    }
  )

  results_df <- if (length(resp$results) > 0) {
    do.call(rbind, lapply(resp$results, as.data.frame))
  } else {
    data.frame(
      concept_id = character(),
      label = character(),
      similarity = numeric(),
      tradition = character(),
      text_excerpt = character(),
      stringsAsFactors = FALSE
    )
  }

  structure(
    list(
      query = query,
      traditions = traditions,
      results = results_df,
      model = resp$model %||% engine$model
    ),
    class = "phil_search_results"
  )
}

#' @export
print.phil_search_results <- function(x, ...) {
  cat(sprintf("Phil Search: \"%s\"\n", x$query))
  if (!is.null(x$traditions)) {
    cat(sprintf("  Traditions: %s\n", paste(x$traditions, collapse = ", ")))
  }
  cat(sprintf("  Model: %s\n", x$model))
  n <- nrow(x$results)
  cat(sprintf("  Results: %d\n", n))
  if (n > 0) {
    cat("\n")
    top <- utils::head(x$results, 10)
    for (i in seq_len(nrow(top))) {
      r <- top[i, ]
      cat(sprintf("  %2d. %-20s (%.3f) [%s]\n",
                  i, r$label, r$similarity, r$tradition))
    }
    if (n > 10) cat(sprintf("  ... and %d more\n", n - 10))
  }
  invisible(x)
}

#' @export
plot.phil_search_results <- function(x, type = "tradition_map", ...) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("ggplot2 required for plotting")
  }

  if (nrow(x$results) == 0) {
    message("No results to plot")
    return(invisible(NULL))
  }

  df <- x$results

  if (type == "tradition_map") {
    ggplot2::ggplot(df, ggplot2::aes(x = reorder(.data$label, .data$similarity),
                                      y = .data$similarity,
                                      fill = .data$tradition)) +
      ggplot2::geom_col() +
      ggplot2::coord_flip() +
      ggplot2::labs(title = sprintf("Search: %s", x$query),
                    x = "Concept", y = "Similarity") +
      ggplot2::theme_minimal()
  }
}
