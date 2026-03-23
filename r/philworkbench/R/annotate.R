#' Auto-annotate concept spans in a PhilCorpus
#'
#' Calls the philengine API /annotate endpoint if available, otherwise falls
#' back to simple keyword-based annotation by searching for known concept
#' labels in the text.
#'
#' @param corpus A PhilCorpus object.
#' @param model Model identifier for concept detection.
#' @param engine A phil_engine object.
#' @return Updated PhilCorpus with conceptSpans.
#' @export
phil_annotate <- function(corpus, model = "default", engine = NULL) {
  stopifnot(inherits(corpus, "PhilCorpus"))
  if (is.null(engine)) engine <- philengine::phil_engine()

  if ("original" %in% names(corpus$layers)) {
    texts <- corpus$layers[["original"]]
    if (is.matrix(texts)) texts <- apply(texts, 1, paste, collapse = " ")
  } else {
    stop("No 'original' layer found in corpus")
  }

  text_ids <- if (!is.null(corpus$segmentData) && "text_id" %in% names(corpus$segmentData)) {
    corpus$segmentData$text_id
  } else {
    paste0("t", seq_along(texts))
  }

  # Try API-based annotation first
  spans_df <- tryCatch({
    resp <- httr2::request(paste0(engine$api_url, "/annotate")) |>
      httr2::req_body_json(list(texts = texts, model = model)) |>
      httr2::req_perform()
    result <- httr2::resp_body_json(resp)
    .parse_api_spans(result, text_ids)
  }, error = function(e) {
    message("API not available, falling back to keyword-based annotation")
    .keyword_annotate(texts, text_ids)
  })

  if (nrow(spans_df) > 0) {
    new_spans <- philcore::ConceptSpans(
      text_id = spans_df$text_id,
      start = as.integer(spans_df$start),
      end = as.integer(spans_df$end),
      concept_id = spans_df$concept_id,
      confidence = spans_df$confidence,
      annotator = "auto",
      interpretation_id = ""
    )

    existing <- tryCatch(philcore::conceptSpans(corpus), error = function(e) NULL)
    if (is.null(existing)) {
      philcore::`conceptSpans<-`(corpus, new_spans)
    } else {
      combined <- rbind(as.data.frame(existing), as.data.frame(new_spans))
      philcore::`conceptSpans<-`(corpus,
        structure(combined, class = c("ConceptSpans", "data.frame")))
    }
  } else {
    message("No concept spans found")
    corpus
  }
}

#' Parse API annotation response into a data.frame
#' @param result API response list.
#' @param text_ids Character vector of text IDs.
#' @return data.frame with columns: text_id, start, end, concept_id, confidence.
#' @keywords internal
.parse_api_spans <- function(result, text_ids) {
  spans <- result$spans
  if (is.null(spans) || length(spans) == 0) {
    return(data.frame(text_id = character(), start = integer(),
                      end = integer(), concept_id = character(),
                      confidence = numeric(), stringsAsFactors = FALSE))
  }
  do.call(rbind, lapply(spans, function(s) {
    data.frame(text_id = s$text_id %||% text_ids[1],
               start = s$start, end = s$end,
               concept_id = s$concept_id,
               confidence = s$confidence %||% 0.5,
               stringsAsFactors = FALSE)
  }))
}

#' Keyword-based concept annotation fallback
#'
#' Searches for known concept labels in each text segment and returns
#' matching spans.
#'
#' @param texts Character vector of texts to annotate.
#' @param text_ids Character vector of corresponding text IDs.
#' @return data.frame of concept spans.
#' @keywords internal
.keyword_annotate <- function(texts, text_ids) {
  # Known concept labels (subset for keyword matching)
  concept_labels <- data.frame(
    concept_id = c("phil:C00001", "phil:C00002", "phil:C00003", "phil:C00004",
                   "phil:C00005", "phil:C00006", "phil:C00007", "phil:C00008",
                   "phil:C00009", "phil:C00010", "phil:C00011", "phil:C00012",
                   "phil:C00013", "phil:C00014", "phil:C00015"),
    label = c("being", "nothingness", "dasein", "existence", "essence",
              "substance", "form", "matter", "mind", "consciousness",
              "self", "other", "nature", "reason", "virtue"),
    stringsAsFactors = FALSE
  )

  spans_list <- list()
  for (i in seq_along(texts)) {
    text_lower <- tolower(texts[i])
    for (j in seq_len(nrow(concept_labels))) {
      label <- concept_labels$label[j]
      # Use word-boundary matching
      pattern <- paste0("\\b", label, "\\b")
      matches <- gregexpr(pattern, text_lower, perl = TRUE)[[1]]
      if (matches[1] != -1) {
        for (k in seq_along(matches)) {
          spans_list[[length(spans_list) + 1]] <- data.frame(
            text_id = text_ids[i],
            start = matches[k],
            end = matches[k] + attr(matches, "match.length")[k] - 1L,
            concept_id = concept_labels$concept_id[j],
            confidence = 0.6,
            stringsAsFactors = FALSE
          )
        }
      }
    }
  }

  if (length(spans_list) == 0) {
    data.frame(text_id = character(), start = integer(),
               end = integer(), concept_id = character(),
               confidence = numeric(), stringsAsFactors = FALSE)
  } else {
    do.call(rbind, spans_list)
  }
}

`%||%` <- function(a, b) if (is.null(a)) b else a

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
