#' Get the Phil cache directory path
#' @return Character path to cache directory.
#' @export
phil_cache_path <- function() {
  path <- file.path(rappdirs::user_cache_dir("phil"), "embeddings")
  if (!dir.exists(path)) dir.create(path, recursive = TRUE)
  path
}

#' Clear the Phil embedding cache
#' @return Invisible NULL.
#' @export
phil_clear_cache <- function() {
  path <- phil_cache_path()
  files <- list.files(path, full.names = TRUE)
  if (length(files) > 0) {
    file.remove(files)
    message(sprintf("Removed %d cached files", length(files)))
  } else {
    message("Cache is empty")
  }
  invisible(NULL)
}
