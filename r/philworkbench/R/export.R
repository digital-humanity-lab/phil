#' Export comparison results to LaTeX
#'
#' @param x A phil_comparison or phil_alignment object.
#' @param style Table style: "comparison_table", "summary".
#' @return Character string of LaTeX code.
#' @export
phil_to_latex <- function(x, style = "comparison_table") {
  if (inherits(x, "phil_comparison")) {
    header <- sprintf("\\begin{table}[htbp]\n\\centering\n\\caption{%s vs %s}\n",
                      x$concept_a, x$concept_b)
    body <- "\\begin{tabular}{lr}\n\\hline\nAspect & Similarity \\\\\n\\hline\n"
    for (nm in names(x$scores)) {
      body <- paste0(body, sprintf("%s & %.3f \\\\\n", nm, x$scores[[nm]]))
    }
    body <- paste0(body, "\\hline\nOverall & ", sprintf("%.3f", x$overall), " \\\\\n")
    footer <- "\\hline\n\\end{tabular}\n\\end{table}"
    paste0(header, body, footer)
  } else {
    warning("LaTeX export not yet supported for this object type")
    ""
  }
}

#' Export to BibTeX
#'
#' @param x An object with source references.
#' @return Character string of BibTeX entries.
#' @export
phil_to_bibtex <- function(x) {
  warning("BibTeX export (implementation pending)")
  ""
}

#' Export to various formats
#'
#' @param x A Phil ecosystem object.
#' @param format Output format: "json", "csv", "rdf", "jsonld".
#' @param path Output file path. If NULL, returns string.
#' @return Character string or file path.
#' @export
phil_export <- function(x, format = "json", path = NULL) {
  format <- match.arg(format, c("json", "csv", "rdf", "jsonld"))

  result <- switch(format,
    json = jsonlite::toJSON(x, auto_unbox = TRUE, pretty = TRUE),
    csv = {
      if (is.data.frame(x)) {
        tmp <- tempfile(fileext = ".csv")
        utils::write.csv(x, tmp, row.names = FALSE)
        readLines(tmp)
      } else {
        warning("CSV export requires data.frame input")
        ""
      }
    },
    rdf = { warning("RDF export (implementation pending)"); "" },
    jsonld = { warning("JSON-LD export (implementation pending)"); "" }
  )

  if (!is.null(path)) {
    writeLines(as.character(result), path)
    invisible(path)
  } else {
    result
  }
}
