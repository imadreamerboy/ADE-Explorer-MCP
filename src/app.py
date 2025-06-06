import gradio as gr
from src.openfda_client import get_top_adverse_events, get_drug_event_pair_frequency
from src.plotting import create_bar_chart
import pandas as pd

# --- Formatting Functions ---

def format_top_events_results(data: dict, drug_name: str) -> str:
    """Formats the results for the top adverse events tool."""
    if "error" in data:
        return f"An error occurred: {data['error']}"
    
    if "results" not in data or not data["results"]:
        return f"No adverse event data found for '{drug_name}'. The drug may not be in the database or it might be misspelled."

    header = f"Top Adverse Events for '{drug_name.title()}'\n"
    header += "Source: FDA FAERS via OpenFDA\n"
    header += "Disclaimer: Spontaneous reports do not prove causation. Consult a healthcare professional.\n"
    header += "---------------------------------------------------\n"

    try:
        df = pd.DataFrame(data["results"])
        df = df.rename(columns={"term": "Adverse Event", "count": "Report Count"})
        result_string = df.to_string(index=False)
        return header + result_string
    except Exception as e:
        return f"An error occurred while formatting the data: {e}"

def format_pair_frequency_results(data: dict, drug_name: str, event_name: str) -> str:
    """Formats the results for the drug-event pair frequency tool."""
    if "error" in data:
        return f"An error occurred: {data['error']}"
    
    total_reports = data.get("meta", {}).get("results", {}).get("total", 0)

    result = (
        f"Found {total_reports:,} reports for the combination of "
        f"'{drug_name.title()}' and '{event_name.title()}'.\n\n"
        "Source: FDA FAERS via OpenFDA\n"
        "Disclaimer: Spontaneous reports do not prove causation. Consult a healthcare professional."
    )
    return result

# --- Tool Functions ---

def top_adverse_events_tool(drug_name: str):
    """
    MCP Tool: Finds the top reported adverse events for a given drug.

    Args:
        drug_name (str): The name of the drug to search for.
    
    Returns:
        tuple: A Plotly figure and a formatted string with the top adverse events.
    """
    data = get_top_adverse_events(drug_name)
    chart = create_bar_chart(data, drug_name)
    text_summary = format_top_events_results(data, drug_name)
    return chart, text_summary

def drug_event_stats_tool(drug_name: str, event_name: str):
    """
    MCP Tool: Gets the total number of reports for a specific drug and adverse event pair.

    Args:
        drug_name (str): The name of the drug to search for.
        event_name (str): The name of the adverse event to search for.
    
    Returns:
        str: A formatted string with the total count of reports.
    """
    data = get_drug_event_pair_frequency(drug_name, event_name)
    return format_pair_frequency_results(data, drug_name, event_name)

# --- Gradio Interface ---

interface1 = gr.Interface(
    fn=top_adverse_events_tool,
    inputs=[
        gr.Textbox(
            label="Drug Name", 
            info="Enter a brand or generic drug name (e.g., 'Aspirin', 'Lisinopril')."
        )
    ],
    outputs=[
        gr.Plot(label="Top Adverse Events Chart"),
        gr.Textbox(label="Top Adverse Events (Raw Data)", lines=15)
    ],
    title="Top Adverse Events by Drug",
    description="Find the most frequently reported adverse events for a specific medication.",
    examples=[["Lisinopril"], ["Ozempic"], ["Metformin"]],
)

interface2 = gr.Interface(
    fn=drug_event_stats_tool,
    inputs=[
        gr.Textbox(label="Drug Name", info="e.g., 'Ibuprofen'"),
        gr.Textbox(label="Adverse Event", info="e.g., 'Headache'")
    ],
    outputs=[gr.Textbox(label="Report Count", lines=5)],
    title="Drug/Event Pair Frequency",
    description="Get the total number of reports for a specific drug and adverse event combination.",
    examples=[["Lisinopril", "Cough"], ["Ozempic", "Nausea"]],
)

demo = gr.TabbedInterface(
    [interface1, interface2], 
    ["Top Events", "Event Frequency"],
    title="Medication Adverse-Event Explorer"
)

if __name__ == "__main__":
    demo.launch(mcp_server=True, server_name="0.0.0.0") 