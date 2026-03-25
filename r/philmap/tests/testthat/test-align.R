test_that("phil_align returns phil_alignment object", {
  # This will fail to connect to API but should handle gracefully
  result <- phil_align("test_a", "test_b", method = "hybrid")
  expect_s3_class(result, "phil_alignment")
  expect_true(is.na(result$similarity))  # API not available
  expect_equal(result$method, "hybrid")
})

test_that("phil_compare returns phil_comparison", {
  result <- phil_compare("concept_a", "concept_b", aspects = "semantic")
  expect_s3_class(result, "phil_comparison")
})
