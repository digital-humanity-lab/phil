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
    rv <- shiny::reactiveValues(corpus = corpus)

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
  }

  shiny::shinyApp(ui, server, options = list(port = port))
}
