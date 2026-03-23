#' Embed texts using the Phil engine
#'
#' @param engine A phil_engine object.
#' @param texts Character vector of texts to embed.
#' @return Numeric matrix with rows = texts, cols = embedding dimensions.
#' @export
phil_embed <- function(engine, texts) {
  stopifnot(inherits(engine, "phil_engine"))

  body <- list(texts = texts, model = engine$model)
  resp <- .api_post(engine$api_url, "/embed", body)

  do.call(rbind, resp$embeddings)
}

#' Embed all segments in a PhilCorpus
#'
#' @param engine A phil_engine object.
#' @param corpus A PhilCorpus object.
#' @param layer_name Name for the embedding layer.
#' @return Updated PhilCorpus with embedding layer added.
#' @export
phil_embed_corpus <- function(engine, corpus, layer_name = "embedding") {
  stopifnot(inherits(engine, "phil_engine"))
  stopifnot(inherits(corpus, "PhilCorpus"))

  # Get text content from original layer or segment data
  if ("original" %in% names(corpus$layers)) {
    texts <- corpus$layers[["original"]]
    if (is.matrix(texts)) texts <- apply(texts, 1, paste, collapse = " ")
  } else {
    stop("No 'original' layer found in corpus. Add text content first.")
  }

  embeddings <- phil_embed(engine, texts)
  philcore::phil_add_layer(corpus, layer_name, embeddings)
}

# Internal: POST to philapi
.api_post <- function(base_url, path, body) {
  req <- httr2::request(paste0(base_url, path)) |>
    httr2::req_body_json(body) |>
    httr2::req_headers("Content-Type" = "application/json")

  tryCatch({
    resp <- httr2::req_perform(req)
    httr2::resp_body_json(resp)
  }, error = function(e) {
    stop(sprintf("philapi request failed (%s%s): %s", base_url, path, e$message))
  })
}
