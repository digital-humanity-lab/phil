#' List available embedding backends
#' @return data.frame of backends with name, description, and requirements.
#' @export
phil_list_backends <- function() {
  data.frame(
    name = c("sentence-transformers", "openai", "cohere", "local"),
    description = c(
      "Local sentence-transformers models (default)",
      "OpenAI text-embedding API",
      "Cohere embed-multilingual API",
      "Local LLM via vLLM/llama.cpp"
    ),
    requires = c("torch, sentence-transformers", "openai API key", "cohere API key", "vLLM server"),
    stringsAsFactors = FALSE
  )
}

#' Compare embedding backends on a benchmark
#'
#' @param engines Named list of phil_engine objects.
#' @param benchmark Benchmark dataset (data.frame with concept pairs and expected similarities).
#' @param metrics Character vector of metrics: "spearman", "pearson", "precision_at_k".
#' @return data.frame with benchmark results per engine.
#' @export
phil_compare_backends <- function(engines, benchmark, metrics = c("spearman", "pearson")) {
  stopifnot(is.list(engines))

  results <- data.frame(
    backend = character(),
    model = character(),
    spearman = numeric(),
    pearson = numeric(),
    stringsAsFactors = FALSE
  )

  for (nm in names(engines)) {
    eng <- engines[[nm]]
    # Embed concept pairs
    tryCatch({
      emb_a <- phil_embed(eng, benchmark$concept_a_text)
      emb_b <- phil_embed(eng, benchmark$concept_b_text)
      computed_sims <- rowSums(emb_a * emb_b)
      expected_sims <- benchmark$expected_similarity

      row <- data.frame(
        backend = nm,
        model = eng$model,
        spearman = cor(computed_sims, expected_sims, method = "spearman"),
        pearson = cor(computed_sims, expected_sims, method = "pearson"),
        stringsAsFactors = FALSE
      )
      results <- rbind(results, row)
    }, error = function(e) {
      warning(sprintf("Backend '%s' failed: %s", nm, e$message))
    })
  }

  results
}
