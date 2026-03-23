#' Compare two philosophical concepts
#'
#' Performs a multi-aspect comparison including semantic, structural,
#' argumentative, and historical dimensions.
#'
#' @param concept_a Concept identifier or label.
#' @param concept_b Concept identifier or label.
#' @param aspects Aspects to compare.
#' @param engine A phil_engine object.
#' @return A phil_comparison S3 object.
#' @export
phil_compare <- function(concept_a, concept_b,
                         aspects = c("semantic", "structural", "argumentative", "historical"),
                         engine = NULL) {
  aspects <- match.arg(aspects, several.ok = TRUE)

  results <- list()
  for (aspect in aspects) {
    alignment <- phil_align(concept_a, concept_b, method = aspect, engine = engine)
    results[[aspect]] <- alignment$similarity
  }

  structure(
    list(
      concept_a = concept_a,
      concept_b = concept_b,
      aspects = aspects,
      scores = results,
      overall = mean(unlist(results), na.rm = TRUE)
    ),
    class = "phil_comparison"
  )
}

#' @export
print.phil_comparison <- function(x, ...) {
  cat(sprintf("Phil Comparison: %s vs %s\n", x$concept_a, x$concept_b))
  cat(sprintf("  Overall similarity: %.3f\n", x$overall))
  cat("  Aspect scores:\n")
  for (nm in names(x$scores)) {
    val <- x$scores[[nm]]
    bar <- paste(rep("#", round(val * 20)), collapse = "")
    cat(sprintf("    %-15s %.3f %s\n", nm, val, bar))
  }
  invisible(x)
}

#' @export
plot.phil_comparison <- function(x, type = "radar", ...) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("ggplot2 required for plotting")
  }

  scores_df <- data.frame(
    aspect = names(x$scores),
    score = unlist(x$scores),
    stringsAsFactors = FALSE
  )

  if (type == "bar") {
    ggplot2::ggplot(scores_df, ggplot2::aes(x = .data$aspect, y = .data$score)) +
      ggplot2::geom_col(fill = "steelblue") +
      ggplot2::coord_flip() +
      ggplot2::ylim(0, 1) +
      ggplot2::labs(
        title = sprintf("%s vs %s", x$concept_a, x$concept_b),
        x = "Aspect", y = "Similarity"
      ) +
      ggplot2::theme_minimal()
  } else {
    # Default bar chart (radar requires additional package)
    plot.phil_comparison(x, type = "bar", ...)
  }
}
