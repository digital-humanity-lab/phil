#' Load a PhilCorpus
#'
#' Load a PhilCorpus from a local file, directory, or PhilCorpusHub identifier.
#'
#' @param source Path to .rds/.h5phil file, or a PhilCorpusHub identifier
#'   (e.g., "watsuji_rinrigaku").
#' @param section Optional section filter (e.g., chapter name).
#' @return A PhilCorpus object.
#' @export
phil_load <- function(source, section = NULL) {
  if (file.exists(source)) {
    if (grepl("\\.rds$", source)) {
      corpus <- readRDS(source)
    } else if (grepl("\\.json$", source)) {
      raw <- jsonlite::fromJSON(source, simplifyVector = FALSE)
      corpus <- .json_to_philcorpus(raw)
    } else {
      stop("Unsupported file format: ", tools::file_ext(source))
    }
  } else {
    corpus <- .hub_load(source)
  }

  if (!is.null(section) && nrow(corpus$segmentData) > 0 &&
      "section" %in% names(corpus$segmentData)) {
    idx <- corpus$segmentData$section == section
    corpus <- corpus[idx, ]
  }

  corpus
}

#' Save a PhilCorpus
#'
#' @param corpus A PhilCorpus object.
#' @param path Output file path (.rds or .json).
#' @export
phil_save <- function(corpus, path) {
  stopifnot(inherits(corpus, "PhilCorpus"))
  if (grepl("\\.rds$", path)) {
    saveRDS(corpus, path)
  } else if (grepl("\\.json$", path)) {
    jsonlite::write_json(unclass(corpus), path, auto_unbox = TRUE, pretty = TRUE)
  } else {
    stop("Unsupported format. Use .rds or .json")
  }
  invisible(path)
}

# Internal: load from hub (stub)
.hub_load <- function(identifier) {
  warning("PhilCorpusHub not yet configured. Returning empty PhilCorpus for: ", identifier)
  PhilCorpus(provenance = list(source = identifier))
}

# Internal: JSON to PhilCorpus
.json_to_philcorpus <- function(raw) {
  PhilCorpus(
    layers = raw$layers %||% list(),
    segmentData = as.data.frame(do.call(rbind, raw$segmentData) %||% data.frame()),
    textMetadata = as.data.frame(do.call(rbind, raw$textMetadata) %||% data.frame()),
    provenance = raw$provenance %||% list()
  )
}

`%||%` <- function(a, b) if (is.null(a)) b else a
