#' Connect to the traditions database
#' @param db_path Path to SQLite database.
#' @return A phil_traditions_db connection object.
#' @export
phil_traditions_db <- function(db_path = NULL) {
  if (is.null(db_path)) {
    db_path <- system.file("extdata", "phil_traditions.sqlite",
                           package = "phil.traditions.db")
    if (db_path == "") {
      stop("Bundled database not found. Build with scripts/build_tradition_db.R")
    }
  }
  con <- DBI::dbConnect(RSQLite::SQLite(), db_path)
  structure(list(con = con, path = db_path), class = "phil_traditions_db")
}
