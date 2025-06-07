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

A Gradio app that exposes a drug-event query tool as an MCP server. It has two core workflows: 
(A) finding top adverse events for a drug, and 
(B) checking the frequency of a specific drug-event pair. 

It uses public data from OpenFDA.

**Hackathon Track:** `mcp-server-track`

---

## Usage

This application provides two tools, accessible via a tabbed interface or as MCP endpoints:

1.  **Top Events**: For a given drug name, it returns a list and a bar chart of the top 10 most frequently reported adverse events.
2.  **Event Frequency**: For a given drug and adverse event pair, it returns the total number of reports found.

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

The server exposes two tools: `top_adverse_events_tool(drug_name)` and `drug_event_stats_tool(drug_name, event_name)`.

---

## Data Source and Disclaimer

*   **Source**: All data is sourced from the public [FDA Adverse Event Reporting System (FAERS)](https://open.fda.gov/data/faers/) via the OpenFDA API.
*   **Disclaimer**: The information provided by this tool is for informational purposes only and is based on spontaneous reports. It does not represent verified medical data or clinical proof of a causal relationship. **Always consult a qualified healthcare professional for medical advice.**