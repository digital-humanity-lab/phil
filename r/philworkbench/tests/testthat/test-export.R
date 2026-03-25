test_that("phil_to_latex generates LaTeX for comparison", {
  comp <- structure(list(
    concept_a = "aidagara", concept_b = "Mitsein",
    scores = list(semantic = 0.82, structural = 0.64),
    overall = 0.73
  ), class = "phil_comparison")

  latex <- phil_to_latex(comp)
  expect_true(grepl("\\\\begin\\{table\\}", latex))
  expect_true(grepl("aidagara", latex))
  expect_true(grepl("0.820", latex))
})

test_that("phil_session_info returns version info", {
  info <- phil_session_info()
  expect_true("r_version" %in% names(info))
  expect_true("timestamp" %in% names(info))
})

test_that("phil_config stores settings", {
  phil_config(api_url = "http://test:9999")
  config <- phil_config()
  expect_equal(config$api_url, "http://test:9999")
  # Reset
  phil_config(api_url = "http://localhost:8000")
})
