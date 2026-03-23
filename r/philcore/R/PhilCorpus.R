#' Create a PhilCorpus object
#'
#' A SummarizedExperiment-like data container for philosophical texts.
#' Stores text layers (original, embeddings, features), segment metadata,
#' text metadata, concept annotations, and provenance information.
#'
#' @param layers Named list of matrices. Each matrix has rows = segments,
#'   cols = texts or features. Common layers: "original", "embedding", "features".
#' @param segmentData data.frame with segment metadata. Required columns:
#'   segment_id, text_id, position, section, segment_type.
#' @param textMetadata data.frame with text metadata. Required columns:
#'   text_id, title, author, year, tradition, language.
#' @param conceptSpans A ConceptSpans object or NULL.
#' @param provenance Named list with provenance info (source, built_with, etc.)
#' @return A PhilCorpus S3 object.
#' @export
PhilCorpus <- function(layers = list(),
                       segmentData = data.frame(),
                       textMetadata = data.frame(),
                       conceptSpans = NULL,
                       provenance = list()) {
  if (!is.list(layers)) stop("layers must be a named list")
  if (!is.data.frame(segmentData)) stop("segmentData must be a data.frame")
  if (!is.data.frame(textMetadata)) stop("textMetadata must be a data.frame")

  obj <- structure(
    list(
      layers = layers,
      segmentData = segmentData,
      textMetadata = textMetadata,
      conceptSpans = conceptSpans,
      provenance = provenance
    ),
    class = "PhilCorpus"
  )
  obj
}

#' @export
print.PhilCorpus <- function(x, ...) {
  n_seg <- n_segments(x)
  n_txt <- n_texts(x)
  n_layers <- length(x$layers)
  layer_names <- if (n_layers > 0) paste(names(x$layers), collapse = ", ") else "(none)"

  traditions <- if (nrow(x$textMetadata) > 0 && "tradition" %in% names(x$textMetadata)) {
    unique(x$textMetadata$tradition)
  } else {
    character(0)
  }

  cat("PhilCorpus object\n")
  cat(sprintf("  %d segments x %d texts x %d layers\n", n_seg, n_txt, n_layers))
  cat(sprintf("  Layers: %s\n", layer_names))
  if (length(traditions) > 0) {
    cat(sprintf("  Traditions: %s\n", paste(traditions, collapse = ", ")))
  }

  if (!is.null(x$conceptSpans)) {
    n_spans <- nrow(as.data.frame(x$conceptSpans))
    cat(sprintf("  ConceptSpans: %d annotations\n", n_spans))
  }
  if (length(x$provenance) > 0 && !is.null(x$provenance$source)) {
    cat(sprintf("  Source: %s\n", x$provenance$source))
  }
  invisible(x)
}

#' @export
summary.PhilCorpus <- function(object, ...) {
  cat("PhilCorpus Summary\n")
  cat(sprintf("  Segments: %d\n", n_segments(object)))
  cat(sprintf("  Texts: %d\n", n_texts(object)))
  cat(sprintf("  Layers: %d\n", length(object$layers)))

  for (nm in names(object$layers)) {
    l <- object$layers[[nm]]
    if (is.matrix(l)) {
      cat(sprintf("    %s: %d x %d matrix\n", nm, nrow(l), ncol(l)))
    } else {
      cat(sprintf("    %s: %s\n", nm, class(l)[1]))
    }
  }

  if (nrow(object$textMetadata) > 0) {
    cat("  Text metadata columns:", paste(names(object$textMetadata), collapse = ", "), "\n")
  }
  invisible(object)
}

#' @export
plot.PhilCorpus <- function(x, type = "overview", ...) {
  if (type == "overview") {
    if (nrow(x$textMetadata) > 0 && "tradition" %in% names(x$textMetadata)) {
      tbl <- table(x$textMetadata$tradition)
      barplot(tbl, main = "Texts by Tradition", las = 2, ...)
    } else {
      message("No tradition metadata available for plotting")
    }
  }
  invisible(x)
}

#' @export
`[.PhilCorpus` <- function(x, i, j, ...) {
  seg <- x$segmentData
  txt <- x$textMetadata
  layers <- x$layers
  spans <- x$conceptSpans

  if (!missing(i)) {
    seg <- seg[i, , drop = FALSE]
    layers <- lapply(layers, function(l) {
      if (is.matrix(l) && nrow(l) >= max(i, na.rm = TRUE)) l[i, , drop = FALSE] else l
    })
  }

  if (!missing(j)) {
    txt <- txt[j, , drop = FALSE]
    layers <- lapply(layers, function(l) {
      if (is.matrix(l) && ncol(l) >= max(j, na.rm = TRUE)) l[, j, drop = FALSE] else l
    })
  }

  PhilCorpus(
    layers = layers,
    segmentData = seg,
    textMetadata = txt,
    conceptSpans = spans,
    provenance = x$provenance
  )
}
