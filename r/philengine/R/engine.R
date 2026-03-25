#' Create a Phil embedding engine
#'
#' @param backend Backend name: "sentence-transformers", "openai", "cohere".
#' @param model Model identifier.
#' @param api_url Base URL for the philapi server.
#' @return A phil_engine S3 object.
#' @export
phil_engine <- function(backend = "sentence-transformers",
                        model = "philmap-e5-finetuned-v2",
                        api_url = "http://localhost:8000") {
  structure(
    list(
      backend = backend,
      model = model,
      api_url = api_url
    ),
    class = "phil_engine"
  )
}

#' @export
print.phil_engine <- function(x, ...) {
  cat("Phil Engine\n")
  cat(sprintf("  Backend: %s\n", x$backend))
  cat(sprintf("  Model: %s\n", x$model))
  cat(sprintf("  API: %s\n", x$api_url))
  invisible(x)
}
