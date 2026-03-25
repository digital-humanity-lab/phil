test_that("tradition_tree prints without error", {
  expect_output(tradition_tree("east_asian"), "japanese")
  expect_output(tradition_tree("western"), "phenomenology")
})
