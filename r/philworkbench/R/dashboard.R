#' Launch the Phil Dashboard
#'
#' Interactive Shiny application for philosophical text analysis.
#' Provides tabs for reading, exploring, comparing, and visualizing.
#'
#' @param corpus Optional PhilCorpus to load on startup.
#' @param port Port for the Shiny server.
#' @return Launches Shiny app (does not return).
#' @export
phil_dashboard <- function(corpus = NULL, port = NULL) {
  if (!requireNamespace("shiny", quietly = TRUE)) {
    stop("shiny package required: install.packages('shiny')")
  }

  ui <- shiny::fluidPage(
    shiny::titlePanel("Phil Dashboard"),
    shiny::sidebarLayout(
      shiny::sidebarPanel(
        width = 3,
        shiny::h4("Navigation"),
        shiny::actionButton("tab_read", "Read"),
        shiny::actionButton("tab_explore", "Explore"),
        shiny::actionButton("tab_compare", "Compare"),
        shiny::actionButton("tab_visualize", "Visualize"),
        shiny::hr(),
        shiny::h4("Configuration"),
        shiny::textInput("api_url", "API URL", value = "http://localhost:8000"),
        shiny::selectInput("model", "Model", choices = c("philmap-e5-finetuned-v2"))
      ),
      shiny::mainPanel(
        width = 9,
        shiny::tabsetPanel(
          id = "main_tabs",
          shiny::tabPanel("Read",
            shiny::textInput("source", "Source", placeholder = "Enter text source..."),
            shiny::actionButton("load_btn", "Load"),
            shiny::verbatimTextOutput("corpus_info")
          ),
          shiny::tabPanel("Explore",
            shiny::textInput("explore_query", "Query",
                             placeholder = "e.g., relationship between self and other"),
            shiny::actionButton("explore_btn", "Explore"),
            shiny::plotOutput("explore_plot"),
            shiny::tableOutput("explore_table")
          ),
          shiny::tabPanel("Compare",
            shiny::fluidRow(
              shiny::column(5, shiny::textInput("concept_a", "Concept A")),
              shiny::column(5, shiny::textInput("concept_b", "Concept B")),
              shiny::column(2, shiny::actionButton("compare_btn", "Compare"))
            ),
            shiny::verbatimTextOutput("compare_result"),
            shiny::plotOutput("compare_plot")
          ),
          shiny::tabPanel("Visualize",
            shiny::selectInput("viz_type", "Visualization",
                               choices = c("concept_map", "timeline", "heatmap")),
            shiny::plotOutput("viz_plot", height = "600px")
          )
        )
      )
    )
  )

  server <- function(input, output, session) {
    rv <- shiny::reactiveValues(
      corpus = corpus,
      exploration = NULL,
      comparison = NULL
    )

    # --- Read tab ---
    output$corpus_info <- shiny::renderPrint({
      if (!is.null(rv$corpus)) print(rv$corpus) else cat("No corpus loaded")
    })

    shiny::observeEvent(input$load_btn, {
      shiny::req(input$source)
      tryCatch({
        rv$corpus <- phil_read(input$source)
      }, error = function(e) {
        shiny::showNotification(e$message, type = "error")
      })
    })

    # --- Explore tab ---
    shiny::observeEvent(input$explore_btn, {
      shiny::req(input$explore_query)
      tryCatch({
        engine <- philengine::phil_engine(
          api_url = input$api_url,
          model = input$model
        )
        rv$exploration <- phil_explore(
          query = input$explore_query,
          engine = engine
        )
      }, error = function(e) {
        shiny::showNotification(
          paste("Exploration error:", e$message), type = "error"
        )
      })
    })

    output$explore_table <- shiny::renderTable({
      shiny::req(rv$exploration)
      if (!is.null(rv$exploration$results) && nrow(rv$exploration$results) > 0) {
        utils::head(rv$exploration$results, 20)
      }
    })

    output$explore_plot <- shiny::renderPlot({
      shiny::req(rv$exploration)
      if (!is.null(rv$exploration$results) && nrow(rv$exploration$results) > 0) {
        tryCatch({
          plot(rv$exploration)
        }, error = function(e) {
          plot.new()
          text(0.5, 0.5, paste("Plot error:", e$message))
        })
      }
    })

    # --- Compare tab ---
    shiny::observeEvent(input$compare_btn, {
      shiny::req(input$concept_a, input$concept_b)
      tryCatch({
        engine <- philengine::phil_engine(
          api_url = input$api_url,
          model = input$model
        )
        rv$comparison <- philmap::phil_compare(
          concept_a = input$concept_a,
          concept_b = input$concept_b,
          engine = engine
        )
      }, error = function(e) {
        shiny::showNotification(
          paste("Comparison error:", e$message), type = "error"
        )
      })
    })

    output$compare_result <- shiny::renderPrint({
      if (!is.null(rv$comparison)) {
        print(rv$comparison)
      } else {
        cat("Enter two concepts and click Compare")
      }
    })

    output$compare_plot <- shiny::renderPlot({
      shiny::req(rv$comparison)
      tryCatch({
        scores_df <- data.frame(
          aspect = names(rv$comparison$scores),
          score = unlist(rv$comparison$scores),
          stringsAsFactors = FALSE
        )
        if (requireNamespace("ggplot2", quietly = TRUE)) {
          print(
            ggplot2::ggplot(scores_df,
                            ggplot2::aes(x = reorder(.data$aspect, .data$score),
                                         y = .data$score)) +
              ggplot2::geom_col(fill = "steelblue") +
              ggplot2::coord_flip() +
              ggplot2::ylim(0, 1) +
              ggplot2::labs(
                title = sprintf("%s vs %s (overall: %.3f)",
                                rv$comparison$concept_a,
                                rv$comparison$concept_b,
                                rv$comparison$overall),
                x = "Aspect", y = "Similarity"
              ) +
              ggplot2::theme_minimal()
          )
        } else {
          barplot(scores_df$score, names.arg = scores_df$aspect,
                  main = sprintf("%s vs %s", rv$comparison$concept_a,
                                 rv$comparison$concept_b),
                  ylab = "Similarity", ylim = c(0, 1),
                  col = "steelblue", horiz = TRUE, las = 1)
        }
      }, error = function(e) {
        plot.new()
        text(0.5, 0.5, paste("Plot error:", e$message))
      })
    })
  }

  shiny::shinyApp(ui, server, options = list(port = port))
}
