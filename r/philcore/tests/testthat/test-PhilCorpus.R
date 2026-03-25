test_that("PhilCorpus construction works", {
  corpus <- PhilCorpus(
    layers = list(embedding = matrix(rnorm(30), nrow = 3, ncol = 10)),
    segmentData = data.frame(
      segment_id = paste0("s", 1:3),
      text_id = c("t1", "t1", "t2"),
      position = 1:3,
      section = c("ch1", "ch1", "ch2"),
      segment_type = rep("paragraph", 3)
    ),
    textMetadata = data.frame(
      text_id = c("t1", "t2"),
      title = c("Rinrigaku", "Sein und Zeit"),
      author = c("Watsuji", "Heidegger"),
      year = c(1937L, 1927L),
      tradition = c("watsuji_ethics", "phenomenology"),
      language = c("jpn", "deu")
    ),
    provenance = list(source = "test", built_with = "philcore 0.1.0")
  )

  expect_s3_class(corpus, "PhilCorpus")
  expect_equal(n_segments(corpus), 3)
  expect_equal(n_texts(corpus), 2)
  expect_equal(length(layers(corpus)), 1)
  expect_true(is.matrix(layers(corpus, "embedding")))
})

test_that("PhilCorpus subsetting works", {
  corpus <- PhilCorpus(
    segmentData = data.frame(
      segment_id = paste0("s", 1:4),
      text_id = c("t1", "t1", "t2", "t2")
    ),
    textMetadata = data.frame(
      text_id = c("t1", "t2"),
      title = c("A", "B")
    )
  )

  sub <- corpus[1:2, ]
  expect_equal(n_segments(sub), 2)
})

test_that("ConceptSpans works", {
  spans <- ConceptSpans(
    text_id = c("t1", "t1", "t2"),
    start = c(10L, 50L, 100L),
    end = c(12L, 53L, 105L),
    concept_id = c("phil:C00142", "phil:C00003", "phil:C00142"),
    confidence = c(0.95, 0.80, 0.88),
    annotator = c("model:philmap-e5-v2", "model:philmap-e5-v2", "human:matsui"),
    interpretation_id = c("I001", "I001", "I002")
  )

  expect_s3_class(spans, "ConceptSpans")
  expect_equal(nrow(spans), 3)

  filtered <- filter_by_concept(spans, "phil:C00142")
  expect_equal(nrow(filtered), 2)
})

test_that("PhilCollection works", {
  c1 <- PhilCorpus(segmentData = data.frame(segment_id = "s1", text_id = "t1"),
                   textMetadata = data.frame(text_id = "t1"))
  c2 <- PhilCorpus(segmentData = data.frame(segment_id = "s2", text_id = "t2"),
                   textMetadata = data.frame(text_id = "t2"))

  collection <- PhilCollection(watsuji = c1, heidegger = c2)
  expect_s3_class(collection, "PhilCollection")
  expect_equal(length(corpora(collection)), 2)
})
