# Internal: hardcoded tradition tree data
.tradition_tree_data <- function() {
  list(
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
}

# Internal: approximate period data for traditions
.tradition_periods <- function() {
  list(
    # Top-level
    western = list(start = -600L, end = NA),
    east_asian = list(start = -600L, end = NA),
    south_asian = list(start = -1500L, end = NA),
    islamic = list(start = 700L, end = NA),
    african = list(start = NA_integer_, end = NA),
    # Western sub-traditions
    ancient = list(start = -600L, end = 500L),
    medieval = list(start = 500L, end = 1500L),
    modern = list(start = 1500L, end = 1900L),
    contemporary = list(start = 1900L, end = NA),
    platonism = list(start = -400L, end = NA),
    aristotelianism = list(start = -350L, end = NA),
    stoicism = list(start = -300L, end = 200L),
    epicureanism = list(start = -300L, end = 200L),
    scholasticism = list(start = 1100L, end = 1500L),
    thomism = list(start = 1250L, end = NA),
    rationalism = list(start = 1600L, end = 1800L),
    empiricism = list(start = 1600L, end = 1800L),
    german_idealism = list(start = 1780L, end = 1860L),
    analytic = list(start = 1900L, end = NA),
    continental = list(start = 1900L, end = NA),
    phenomenology = list(start = 1900L, end = NA),
    existentialism = list(start = 1920L, end = 1980L),
    pragmatism = list(start = 1870L, end = NA),
    critical_theory = list(start = 1930L, end = NA),
    poststructuralism = list(start = 1960L, end = NA),
    # East Asian
    chinese = list(start = -600L, end = NA),
    japanese = list(start = 600L, end = NA),
    korean = list(start = 600L, end = NA),
    confucianism = list(start = -500L, end = NA),
    neo_confucianism = list(start = 1000L, end = 1900L),
    new_confucianism = list(start = 1920L, end = NA),
    daoism = list(start = -400L, end = NA),
    chinese_buddhism = list(start = 100L, end = NA),
    legalism = list(start = -400L, end = -200L),
    kyoto_school = list(start = 1910L, end = NA),
    zen_buddhism = list(start = 1200L, end = NA),
    watsuji_ethics = list(start = 1930L, end = 1960L),
    national_learning = list(start = 1700L, end = 1870L),
    korean_confucianism = list(start = 1400L, end = NA),
    korean_buddhism = list(start = 400L, end = NA),
    # South Asian
    hindu = list(start = -1500L, end = NA),
    buddhist = list(start = -500L, end = NA),
    heterodox = list(start = -600L, end = NA),
    vedanta = list(start = -500L, end = NA),
    advaita = list(start = 700L, end = NA),
    yoga = list(start = -200L, end = NA),
    samkhya = list(start = -400L, end = NA),
    nyaya = list(start = -200L, end = NA),
    theravada = list(start = -300L, end = NA),
    madhyamaka = list(start = 150L, end = NA),
    yogacara = list(start = 300L, end = NA),
    tibetan_buddhism = list(start = 700L, end = NA),
    jainism = list(start = -600L, end = NA),
    carvaka = list(start = -600L, end = 1400L),
    # Islamic
    kalam = list(start = 700L, end = NA),
    falsafa = list(start = 800L, end = 1200L),
    illuminationist = list(start = 1150L, end = NA),
    ashari = list(start = 900L, end = NA),
    mutazili = list(start = 750L, end = 1100L),
    avicennism = list(start = 1000L, end = NA),
    averroism = list(start = 1150L, end = 1400L),
    ishraqism = list(start = 1170L, end = NA),
    # African
    ubuntu_philosophy = list(start = NA_integer_, end = NA),
    sage_philosophy = list(start = 1970L, end = NA),
    ethnophilosophy = list(start = 1940L, end = NA)
  )
}

#' Display tradition hierarchy as a tree
#'
#' @param root Root tradition to start from. NULL for full tree.
#' @param db A phil_traditions_db object.
#' @export
tradition_tree <- function(root = NULL, db = NULL) {
  tree <- .tradition_tree_data()

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
#'
#' Returns the immediate children of a tradition node in the hierarchy.
#'
#' @param tradition_id Tradition identifier.
#' @return Character vector of children.
#' @export
tradition_children <- function(tradition_id) {
  tree <- .tradition_tree_data()

  # Check top-level
  if (tradition_id %in% names(tree)) {
    node <- tree[[tradition_id]]
    if (is.list(node)) {
      return(names(node))
    } else {
      return(node)
    }
  }

  # Search second level
  for (top in names(tree)) {
    if (is.list(tree[[top]]) && tradition_id %in% names(tree[[top]])) {
      node <- tree[[top]][[tradition_id]]
      if (is.list(node)) {
        return(names(node))
      } else {
        return(node)
      }
    }
  }

  # It is a leaf or not found
  character(0)
}

#' Get ancestor traditions
#'
#' Returns the ancestor chain from root to the parent of the given tradition.
#'
#' @param tradition_id Tradition identifier.
#' @return Character vector of ancestors (root first).
#' @export
tradition_ancestors <- function(tradition_id) {
  tree <- .tradition_tree_data()

  # Top-level nodes have no ancestors
  if (tradition_id %in% names(tree)) {
    return(character(0))
  }

  # Search second level (direct children of top-level)
  for (top in names(tree)) {
    if (is.list(tree[[top]])) {
      if (tradition_id %in% names(tree[[top]])) {
        return(top)
      }
      # Search third level (leaf values)
      for (mid in names(tree[[top]])) {
        node <- tree[[top]][[mid]]
        if (is.character(node) && tradition_id %in% node) {
          return(c(top, mid))
        }
      }
    } else {
      # top-level has character vector children (e.g., african)
      if (tradition_id %in% tree[[top]]) {
        return(top)
      }
    }
  }

  character(0)
}

#' Get time period for a tradition
#'
#' Returns approximate start and end years for a philosophical tradition.
#'
#' @param tradition_id Tradition identifier.
#' @return Named list with start and end years (end = NA if ongoing).
#' @export
tradition_period <- function(tradition_id) {
  periods <- .tradition_periods()
  if (tradition_id %in% names(periods)) {
    periods[[tradition_id]]
  } else {
    list(start = NA_integer_, end = NA_integer_)
  }
}
