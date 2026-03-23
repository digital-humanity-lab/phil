#' Compute text features for a PhilCorpus
#'
#' @param corpus A PhilCorpus object.
#' @param type Feature types: "lexical", "structural", "intertextual", "all".
#' @param engine Optional phil_engine for embedding-based features.
#' @return Matrix of features, or updated PhilCorpus if corpus is provided.
#' @export
phil_quantify <- function(corpus, type = "lexical", engine = NULL) {
  stopifnot(inherits(corpus, "PhilCorpus"))

  type <- match.arg(type, c("lexical", "structural", "intertextual", "all"),
                    several.ok = TRUE)
  if ("all" %in% type) type <- c("lexical", "structural", "intertextual")

  if ("original" %in% names(corpus$layers)) {
    texts <- corpus$layers[["original"]]
    if (is.matrix(texts)) texts <- apply(texts, 1, paste, collapse = " ")
  } else {
    stop("No 'original' layer found")
  }

  features_list <- list()
  if ("lexical" %in% type) {
    features_list[["lexical"]] <- .compute_lexical(texts)
  }
  if ("structural" %in% type) {
    features_list[["structural"]] <- .compute_structural(texts)
  }
  if ("intertextual" %in% type && !is.null(engine)) {
    features_list[["intertextual"]] <- .compute_intertextual(texts, engine)
  }

  features <- do.call(cbind, features_list)
  philcore::phil_add_layer(corpus, "features", features)
}

.compute_lexical <- function(texts) {
  n <- length(texts)
  result <- matrix(0, nrow = n, ncol = 4,
                   dimnames = list(NULL, c("n_tokens", "n_types", "ttr", "mean_word_length")))
  for (i in seq_along(texts)) {
    tokens <- unlist(strsplit(texts[i], "\\s+"))
    n_tok <- length(tokens)
    n_typ <- length(unique(tokens))
    result[i, "n_tokens"] <- n_tok
    result[i, "n_types"] <- n_typ
    result[i, "ttr"] <- if (n_tok > 0) n_typ / n_tok else 0
    result[i, "mean_word_length"] <- if (n_tok > 0) mean(nchar(tokens)) else 0
  }
  result
}

.compute_structural <- function(texts) {
  n <- length(texts)
  markers <- c("therefore", "because", "however", "thus", "hence",
               "although", "nevertheless", "moreover", "furthermore")
  result <- matrix(0, nrow = n, ncol = 2,
                   dimnames = list(NULL, c("n_sentences", "argument_marker_density")))
  for (i in seq_along(texts)) {
    sents <- unlist(strsplit(texts[i], "[.!?]+"))
    result[i, "n_sentences"] <- length(sents)
    tokens_lower <- tolower(unlist(strsplit(texts[i], "\\s+")))
    n_markers <- sum(tokens_lower %in% markers)
    result[i, "argument_marker_density"] <- if (length(tokens_lower) > 0) {
      n_markers / length(tokens_lower)
    } else 0
  }
  result
}

.compute_intertextual <- function(texts, engine) {
  # Requires embedding; compute pairwise novelty
  embeddings <- phil_embed(engine, texts)
  n <- nrow(embeddings)
  novelty <- numeric(n)
  for (i in seq_len(n)) {
    sims <- as.numeric(embeddings %*% embeddings[i, ])
    sims[i] <- 0
    novelty[i] <- 1 - max(sims)
  }
  matrix(novelty, ncol = 1, dimnames = list(NULL, "novelty_score"))
}
