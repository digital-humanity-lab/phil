#' Align two philosophical concepts
#'
#' @param concept_a Concept identifier or label.
#' @param concept_b Concept identifier or label.
#' @param method Alignment method: "semantic", "structural", "argumentative", "hybrid".
#' @param engine A phil_engine object. If NULL, uses default.
#' @return A phil_alignment S3 object.
#' @export
phil_align <- function(concept_a, concept_b,
                       method = c("hybrid", "semantic", "structural", "argumentative"),
                       engine = NULL) {
  method <- match.arg(method)

  if (is.null(engine)) engine <- philengine::phil_engine()

  body <- list(
    concept_a = concept_a,
    concept_b = concept_b,
    method = method
  )

  resp <- tryCatch(
    .api_post(engine$api_url, "/compare", body),
    error = function(e) {
      list(similarity = NA_real_, method = method,
           facet_scores = list(), evidence = list(),
           error = e$message)
    }
  )

  structure(
    list(
      concept_a = concept_a,
      concept_b = concept_b,
      method = method,
      similarity = resp$similarity %||% NA_real_,
      facet_scores = resp$facet_scores %||% list(),
      evidence = resp$evidence %||% list()
    ),
    class = "phil_alignment"
  )
}

#' @export
print.phil_alignment <- function(x, ...) {
  cat(sprintf("Phil Alignment: %s <-> %s\n", x$concept_a, x$concept_b))
  cat(sprintf("  Method: %s\n", x$method))
  cat(sprintf("  Similarity: %.3f\n", x$similarity))
  if (length(x$facet_scores) > 0) {
    cat("  Facet scores:\n")
    for (nm in names(x$facet_scores)) {
      cat(sprintf("    %s: %.3f\n", nm, x$facet_scores[[nm]]))
    }
  }
  invisible(x)
}

#' @export
summary.phil_alignment <- function(object, ...) {
  print(object)
}

`%||%` <- function(a, b) if (is.null(a)) b else a

.api_post <- function(base_url, path, body) {
  req <- httr2::request(paste0(base_url, path)) |>
    httr2::req_body_json(body)
  resp <- httr2::req_perform(req)
  httr2::resp_body_json(resp)
}
