#' Auto-annotate concept spans in a PhilCorpus
#'
#' @param corpus A PhilCorpus object.
#' @param model Model identifier for concept detection.
#' @param engine A phil_engine object.
#' @return Updated PhilCorpus with conceptSpans.
#' @export
phil_annotate <- function(corpus, model = "default", engine = NULL) {
  stopifnot(inherits(corpus, "PhilCorpus"))
  if (is.null(engine)) engine <- philengine::phil_engine()

  # Call annotation API
  message("Auto-annotating concepts (API-based, implementation pending)")
  corpus
}

#' Interactively review annotations
#'
#' Launches an interactive annotation reviewer (Shiny-based).
#'
#' @param corpus A PhilCorpus object with conceptSpans.
#' @return Updated PhilCorpus with reviewed annotations.
#' @export
phil_review <- function(corpus) {
  stopifnot(inherits(corpus, "PhilCorpus"))
  if (!requireNamespace("shiny", quietly = TRUE)) {
    stop("shiny package required for interactive review")
  }
  message("Interactive review (Shiny UI, implementation pending)")
  corpus
}

#' Manually tag a concept span
#'
#' @param corpus A PhilCorpus object.
#' @param concept_id Concept identifier.
#' @param text_id Text identifier.
#' @param start Start position.
#' @param end End position.
#' @param annotator Annotator identifier.
#' @param interpretation_id Interpretation layer.
#' @return Updated PhilCorpus.
#' @export
phil_tag <- function(corpus, concept_id, text_id, start, end,
                     annotator = "human", interpretation_id = "") {
  stopifnot(inherits(corpus, "PhilCorpus"))

  new_span <- philcore::ConceptSpans(
    text_id = text_id,
    start = as.integer(start),
    end = as.integer(end),
    concept_id = concept_id,
    confidence = 1.0,
    annotator = annotator,
    interpretation_id = interpretation_id
  )

  existing <- philcore::conceptSpans(corpus)
  if (is.null(existing)) {
    philcore::`conceptSpans<-`(corpus, new_span)
  } else {
    combined <- rbind(as.data.frame(existing), as.data.frame(new_span))
    philcore::`conceptSpans<-`(corpus,
      structure(combined, class = c("ConceptSpans", "data.frame")))
  }
}
