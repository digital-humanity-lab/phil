test_that("phil_concepts_db connects", {
  skip_if_not(file.exists(system.file("extdata", "phil_concepts.sqlite", package = "phil.concepts.db")))
  db <- phil_concepts_db()
  expect_s3_class(db, "phil_concepts_db")
})

test_that("keytypes returns expected types", {
  types <- keytypes(NULL)
  expect_true("CONCEPT_ID" %in% types)
  expect_true("LABEL_EN" %in% types)
})
