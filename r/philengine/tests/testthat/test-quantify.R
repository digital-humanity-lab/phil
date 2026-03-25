test_that("phil_quantify computes lexical features", {
  corpus <- philcore::PhilCorpus(
    layers = list(original = c("This is a test sentence with some words.",
                                "Another sentence here.")),
    segmentData = data.frame(segment_id = c("s1", "s2"), text_id = c("t1", "t1")),
    textMetadata = data.frame(text_id = "t1", title = "Test")
  )
  # Test .compute_lexical directly
  result <- philengine:::.compute_lexical(c("Hello world hello", "Testing one two three"))
  expect_equal(nrow(result), 2)
  expect_equal(ncol(result), 4)
  expect_equal(colnames(result), c("n_tokens", "n_types", "ttr", "mean_word_length"))
  expect_equal(result[1, "n_tokens"], 3)
  expect_equal(result[1, "n_types"], 2)  # "hello" appears twice
})

test_that("phil_engine creates engine object", {
  engine <- phil_engine()
  expect_s3_class(engine, "phil_engine")
  expect_equal(engine$backend, "sentence-transformers")
})

test_that("phil_list_backends returns data.frame", {
  backends <- phil_list_backends()
  expect_s3_class(backends, "data.frame")
  expect_true("sentence-transformers" %in% backends$name)
})
