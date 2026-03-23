#' @title PhilCorpus Accessors
#' @name accessors
#' @description Accessor functions for PhilCorpus components.

#' Get or set layers
#' @param x A PhilCorpus object.
#' @param name Optional layer name. If NULL, returns all layers.
#' @param value Replacement value.
#' @export
layers <- function(x, name = NULL) {
  stopifnot(inherits(x, "PhilCorpus"))
  if (is.null(name)) x$layers else x$layers[[name]]
}

#' @rdname accessors
#' @export
`layers<-` <- function(x, value) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$layers <- value
  x
}

#' @rdname accessors
#' @export
segmentData <- function(x) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$segmentData
}

#' @rdname accessors
#' @export
`segmentData<-` <- function(x, value) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$segmentData <- value
  x
}

#' @rdname accessors
#' @export
textMetadata <- function(x) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$textMetadata
}

#' @rdname accessors
#' @export
`textMetadata<-` <- function(x, value) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$textMetadata <- value
  x
}

#' @rdname accessors
#' @export
conceptSpans <- function(x, interpretation = NULL) {
  stopifnot(inherits(x, "PhilCorpus"))
  spans <- x$conceptSpans
  if (!is.null(interpretation) && !is.null(spans)) {
    spans <- filter_by_interpretation(spans, interpretation)
  }
  spans
}

#' @rdname accessors
#' @export
`conceptSpans<-` <- function(x, value) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$conceptSpans <- value
  x
}

#' @rdname accessors
#' @export
provenance <- function(x) {
  stopifnot(inherits(x, "PhilCorpus"))
  x$provenance
}

#' Number of segments in a PhilCorpus
#' @param x A PhilCorpus object.
#' @return Integer.
#' @export
n_segments <- function(x) {
  stopifnot(inherits(x, "PhilCorpus"))
  nrow(x$segmentData)
}

#' Number of texts in a PhilCorpus
#' @param x A PhilCorpus object.
#' @return Integer.
#' @export
n_texts <- function(x) {
  stopifnot(inherits(x, "PhilCorpus"))
  nrow(x$textMetadata)
}

#' Add a layer to a PhilCorpus
#' @param corpus A PhilCorpus object.
#' @param name Layer name.
#' @param value Matrix or data to add as a layer.
#' @return Updated PhilCorpus.
#' @export
phil_add_layer <- function(corpus, name, value) {
  stopifnot(inherits(corpus, "PhilCorpus"))
  corpus$layers[[name]] <- value
  corpus
}
