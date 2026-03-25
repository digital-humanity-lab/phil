# Internal config environment
.phil_env <- new.env(parent = emptyenv())
.phil_env$api_url <- "http://localhost:8000"
.phil_env$default_model <- "philmap-e5-finetuned-v2"
.phil_env$cache_dir <- NULL

#' Configure Phil ecosystem settings
#'
#' @param api_url Base URL for the philapi server.
#' @param default_model Default embedding model.
#' @param cache_dir Cache directory path.
#' @return Invisibly returns current configuration as a list.
#' @export
phil_config <- function(api_url = NULL, default_model = NULL, cache_dir = NULL) {
  if (!is.null(api_url)) .phil_env$api_url <- api_url
  if (!is.null(default_model)) .phil_env$default_model <- default_model
  if (!is.null(cache_dir)) .phil_env$cache_dir <- cache_dir

  config <- list(
    api_url = .phil_env$api_url,
    default_model = .phil_env$default_model,
    cache_dir = .phil_env$cache_dir
  )

  invisible(config)
}

#' Get Phil session info
#'
#' @return List with version, config, and reproducibility info.
#' @export
phil_session <- function() {
  list(
    config = phil_config(),
    session = phil_session_info(),
    reproducibility_hash = digest::digest(list(
      phil_config(), Sys.time()), algo = "md5")
  )
}
