#' Display tradition hierarchy as a tree
#'
#' @param root Root tradition to start from. NULL for full tree.
#' @param db A phil_traditions_db object.
#' @export
tradition_tree <- function(root = NULL, db = NULL) {
  # Hardcoded tree for now; will be backed by SQLite
  tree <- list(
    western = list(
      ancient = c("platonism", "aristotelianism", "stoicism", "epicureanism"),
      medieval = c("scholasticism", "thomism"),
      modern = c("rationalism", "empiricism", "german_idealism"),
      contemporary = c("analytic", "continental", "phenomenology",
                       "existentialism", "pragmatism", "critical_theory",
                       "poststructuralism")
    ),
    east_asian = list(
      chinese = c("confucianism", "neo_confucianism", "new_confucianism",
                   "daoism", "chinese_buddhism", "legalism"),
      japanese = c("kyoto_school", "zen_buddhism", "watsuji_ethics",
                    "national_learning"),
      korean = c("korean_confucianism", "korean_buddhism")
    ),
    south_asian = list(
      hindu = c("vedanta", "advaita", "yoga", "samkhya", "nyaya"),
      buddhist = c("theravada", "madhyamaka", "yogacara", "tibetan_buddhism"),
      heterodox = c("jainism", "carvaka")
    ),
    islamic = list(
      kalam = c("ashari", "mutazili"),
      falsafa = c("avicennism", "averroism"),
      illuminationist = c("ishraqism")
    ),
    african = c("ubuntu_philosophy", "sage_philosophy", "ethnophilosophy")
  )

  .print_tree <- function(node, indent = 0) {
    prefix <- paste(rep("  ", indent), collapse = "")
    if (is.list(node)) {
      for (nm in names(node)) {
        cat(sprintf("%s%s\n", prefix, nm))
        .print_tree(node[[nm]], indent + 1)
      }
    } else {
      for (val in node) {
        cat(sprintf("%s%s\n", prefix, val))
      }
    }
  }

  if (is.null(root)) {
    .print_tree(tree)
  } else if (root %in% names(tree)) {
    cat(sprintf("%s\n", root))
    .print_tree(tree[[root]], 1)
  } else {
    # Search deeper
    for (top in names(tree)) {
      if (is.list(tree[[top]]) && root %in% names(tree[[top]])) {
        cat(sprintf("%s\n", root))
        .print_tree(tree[[top]][[root]], 1)
        return(invisible(NULL))
      }
    }
    message(sprintf("Tradition '%s' not found", root))
  }
  invisible(NULL)
}

#' Get child traditions
#' @param tradition_id Tradition identifier.
#' @return Character vector of children.
#' @export
tradition_children <- function(tradition_id) {
  # Stub - will be backed by SQLite
  character(0)
}

#' Get ancestor traditions
#' @param tradition_id Tradition identifier.
#' @return Character vector of ancestors (root first).
#' @export
tradition_ancestors <- function(tradition_id) {
  # Stub
  character(0)
}

#' Get time period for a tradition
#' @param tradition_id Tradition identifier.
#' @return Named list with start and end years.
#' @export
tradition_period <- function(tradition_id) {
  list(start = NA_integer_, end = NA_integer_)
}
