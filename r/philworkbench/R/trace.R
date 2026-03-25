#' Trace concept genealogy and influence
#'
#' If the philgraph API is available, queries for the concept's neighbors
#' in the knowledge graph. Otherwise, falls back to returning data from
#' phil.concepts.db RELATED_CONCEPTS field.
#'
#' @param concept Concept ID or label.
#' @param depth Depth of influence network to trace.
#' @param engine A phil_engine object.
#' @return A phil_genealogy S3 object.
#' @export
phil_trace <- function(concept, depth = 2, engine = NULL) {
  if (is.null(engine)) engine <- philengine::phil_engine()

  # Try philgraph API first
  genealogy <- tryCatch({
    .trace_api(concept, depth, engine)
  }, error = function(e) {
    # Fall back to phil.concepts.db
    .trace_db(concept, depth)
  })

  genealogy
}

#' Trace via philgraph API
#' @keywords internal
.trace_api <- function(concept, depth, engine) {
  resp <- httr2::request(paste0(engine$api_url, "/graph/neighbors")) |>
    httr2::req_body_json(list(concept = concept, depth = depth)) |>
    httr2::req_perform()
  result <- httr2::resp_body_json(resp)

  nodes <- if (length(result$nodes) > 0) {
    do.call(rbind, lapply(result$nodes, function(n) {
      data.frame(concept_id = n$id %||% "",
                 label = n$label %||% "",
                 tradition = n$tradition %||% "",
                 era = n$era %||% "",
                 stringsAsFactors = FALSE)
    }))
  } else {
    data.frame(concept_id = character(), label = character(),
               tradition = character(), era = character(),
               stringsAsFactors = FALSE)
  }

  edges <- if (length(result$edges) > 0) {
    do.call(rbind, lapply(result$edges, function(e) {
      data.frame(from = e$from %||% "",
                 to = e$to %||% "",
                 relation = e$relation %||% "",
                 confidence = e$confidence %||% 0,
                 stringsAsFactors = FALSE)
    }))
  } else {
    data.frame(from = character(), to = character(),
               relation = character(), confidence = numeric(),
               stringsAsFactors = FALSE)
  }

  structure(
    list(concept = concept, depth = depth, nodes = nodes, edges = edges),
    class = "phil_genealogy"
  )
}

#' Trace via phil.concepts.db fallback
#' @keywords internal
.trace_db <- function(concept, depth) {
  nodes <- data.frame(concept_id = character(), label = character(),
                      tradition = character(), era = character(),
                      stringsAsFactors = FALSE)
  edges <- data.frame(from = character(), to = character(),
                      relation = character(), confidence = numeric(),
                      stringsAsFactors = FALSE)

  tryCatch({
    db <- phil.concepts.db::phil_concepts_db()
    # Try to find the concept
    info <- tryCatch(
      phil.concepts.db::select.phil_concepts_db(
        db, keys = concept, keytype = "CONCEPT_ID",
        columns = c("CONCEPT_ID", "LABEL_EN", "TRADITION", "ERA", "RELATED_CONCEPTS")
      ),
      error = function(e) {
        # Try by label
        phil.concepts.db::select.phil_concepts_db(
          db, keys = concept, keytype = "LABEL_EN",
          columns = c("CONCEPT_ID", "LABEL_EN", "TRADITION", "ERA", "RELATED_CONCEPTS")
        )
      }
    )

    if (nrow(info) > 0) {
      # Add root node
      nodes <- rbind(nodes, data.frame(
        concept_id = info$CONCEPT_ID[1],
        label = info$LABEL_EN[1],
        tradition = info$TRADITION[1] %||% "",
        era = info$ERA[1] %||% "",
        stringsAsFactors = FALSE
      ))

      # Parse RELATED_CONCEPTS field
      related_str <- info$RELATED_CONCEPTS[1]
      if (!is.na(related_str) && nchar(related_str) > 0) {
        related_ids <- trimws(unlist(strsplit(related_str, "[,;]")))
        related_ids <- related_ids[nchar(related_ids) > 0]

        for (rid in related_ids) {
          # Add edge
          edges <- rbind(edges, data.frame(
            from = info$CONCEPT_ID[1], to = rid,
            relation = "related", confidence = 0.5,
            stringsAsFactors = FALSE
          ))

          # Try to look up related concept details
          tryCatch({
            rel_info <- phil.concepts.db::select.phil_concepts_db(
              db, keys = rid, keytype = "CONCEPT_ID",
              columns = c("CONCEPT_ID", "LABEL_EN", "TRADITION", "ERA")
            )
            if (nrow(rel_info) > 0) {
              nodes <- rbind(nodes, data.frame(
                concept_id = rel_info$CONCEPT_ID[1],
                label = rel_info$LABEL_EN[1],
                tradition = rel_info$TRADITION[1] %||% "",
                era = rel_info$ERA[1] %||% "",
                stringsAsFactors = FALSE
              ))
            }
          }, error = function(e) NULL)
        }
      }
    }

    DBI::dbDisconnect(db$con)
  }, error = function(e) {
    message(sprintf("phil.concepts.db not available: %s", e$message))
  })

  structure(
    list(concept = concept, depth = depth, nodes = nodes, edges = edges),
    class = "phil_genealogy"
  )
}

`%||%` <- function(a, b) if (is.null(a)) b else a

#' @export
print.phil_genealogy <- function(x, ...) {
  cat(sprintf("Phil Genealogy: %s (depth=%d)\n", x$concept, x$depth))
  cat(sprintf("  Nodes: %d\n", nrow(x$nodes)))
  cat(sprintf("  Edges: %d\n", nrow(x$edges)))
  invisible(x)
}

#' @export
plot.phil_genealogy <- function(x, ...) {
  if (nrow(x$nodes) == 0) {
    message("No genealogy data to plot")
    return(invisible(NULL))
  }
  message("Genealogy visualization (implementation pending)")
  invisible(x)
}
