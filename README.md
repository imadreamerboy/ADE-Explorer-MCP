---
title: Medication Adverse-Event Explorer
emoji: 💊
colorFrom: blue
colorTo: green
sdk: gradio
app_file: app.py
tag: mcp-server-track
short_description: Gradio app that exposes a drug-event tool as an MCP server.
sdk_version: 5.33.0
---

# Medication Adverse-Event Explorer (ADE Explorer)

An interactive Gradio application for exploring and visualizing data from the FDA Adverse Event Reporting System (FAERS). It also functions as an MCP (Model Context Protocol) server, allowing it to be used as a tool by language models.

It was created for the [MCP Hackathon](https://huggingface.co/Agents-MCP-Hackathon) in May 2025.

**Hackathon Track:** `mcp-server-track`

---

## Usage

The explorer is organized into several tabs, each providing a different view of the data:

-   **Top Events:** Find the most frequently reported adverse events for a specific drug. You can filter the results by the number of events to show, patient sex, and age range. The output includes a bar chart and a table with both raw counts and relative frequencies.
-   **Serious Outcomes:** See a breakdown of the most serious outcomes (e.g., hospitalization, death) reported for a drug. The output includes a chart and a table showing the percentage of total serious reports for each outcome.
-   **Event Frequency:** Get the total number of reports for a specific combination of a drug and an adverse event, along with the percentage this combination represents out of all reports for that drug.
-   **Time-Series Trends:** Plot the number of adverse event reports over time for a specific drug and event pair, with options for yearly or quarterly aggregation.
-   **Report Sources:** View a pie chart and data table showing the breakdown of who reported the adverse events (e.g., Consumer, Physician, Pharmacist).

## MCP Server Configuration

To use this application as a tool with an MCP client (like Cursor or Claude Desktop), you first need to run it and get the server URL.

1.  **Run the App**:
    ```bash
    python app.py
    ```
2.  **Find the MCP URL**: The server will start and print the MCP URL in the console. It will look something like this:
    `http://127.0.0.1:7860/gradio_api/mcp/sse`
3.  **Configure Your Client**: Add the following configuration to your MCP client's settings, replacing the URL with the one from the previous step.

    ```json
    {
      "mcpServers": {
        "ade_explorer": {
          "url": "http://127.0.0.1:7860/gradio_api/mcp/sse"
        }
      }
    }
    ```

or for Claude Desktop:

```json
{
  "mcpServers": {
    "ade_explorer": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:7860/gradio_api/mcp/sse",
        "--transport",
        "sse-only"
      ]
    }
  }
}
```

### Exposed MCP Tools

The server exposes the following tools, corresponding to the functionalities in the UI:

-   `top_adverse_events_tool(drug_name: str, top_n: int = 10, patient_sex: str = "all", min_age: int = 0, max_age: int = 120)`: Finds the top reported adverse events for a given drug, with optional filters.
-   `serious_outcomes_tool(drug_name: str, top_n: int = 6)`: Finds the top reported serious outcomes for a given drug.
-   `drug_event_stats_tool(drug_name: str, event_name: str)`: Gets the total number of reports for a specific drug and adverse event pair.
-   `time_series_tool(drug_name: str, event_name: str, aggregation: str)`: Creates a time-series plot for a drug-event pair (`aggregation` can be 'Yearly' or 'Quarterly').
-   `report_source_tool(drug_name: str, top_n: int = 5)`: Creates a pie chart of report sources for a given drug.

---

## Data Source and Disclaimer

*   **Source**: All data is sourced from the public [FDA Adverse Event Reporting System (FAERS)](https://open.fda.gov/data/faers/) via the OpenFDA API.
*   **Disclaimer**: The information provided by this tool is for informational purposes only and is based on spontaneous reports. It does not represent verified medical data or clinical proof of a causal relationship. **Always consult a qualified healthcare professional for medical advice.**