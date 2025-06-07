import gradio as gr
from openfda_client import (
    get_top_adverse_events, 
    get_drug_event_pair_frequency, 
    get_serious_outcomes,
    get_time_series_data,
    get_report_source_data
)
from plotting import (
    create_bar_chart, 
    create_outcome_chart,
    create_time_series_chart,
    create_pie_chart
)
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

def format_serious_outcomes_results(data: dict, drug_name: str) -> str:
    """Formats the results for the serious outcomes tool."""
    if "error" in data:
        return f"An error occurred: {data['error']}"
    
    if "results" not in data or not data["results"]:
        return f"No serious outcome data found for '{drug_name}'. The drug may not be in the database or it might be misspelled."

    header = f"Top Serious Outcomes for '{drug_name.title()}'\n"
    header += "Source: FDA FAERS via OpenFDA\n"
    header += "Disclaimer: Spontaneous reports do not prove causation. Consult a healthcare professional.\n"
    header += "---------------------------------------------------\n"

    try:
        df = pd.DataFrame(data["results"])
        df = df.rename(columns={"term": "Serious Outcome", "count": "Report Count"})
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

def top_adverse_events_tool(drug_name: str, patient_sex: str = "all", min_age: int = 0, max_age: int = 120):
    """
    MCP Tool: Finds the top reported adverse events for a given drug.

    Args:
        drug_name (str): The name of the drug to search for.
        patient_sex (str): The patient's sex to filter by.
        min_age (int): The minimum age for the filter.
        max_age (int): The maximum age for the filter.
    
    Returns:
        tuple: A Plotly figure and a formatted string with the top adverse events.
    """
    sex_code = None
    if patient_sex == "Male":
        sex_code = "1"
    elif patient_sex == "Female":
        sex_code = "2"
    
    age_range = None
    if min_age > 0 or max_age < 120:
        age_range = (min_age, max_age)

    data = get_top_adverse_events(drug_name, patient_sex=sex_code, age_range=age_range)
    chart = create_bar_chart(data, drug_name)
    text_summary = format_top_events_results(data, drug_name)
    return chart, text_summary

def serious_outcomes_tool(drug_name: str):
    """
    MCP Tool: Finds the top reported serious outcomes for a given drug.

    Args:
        drug_name (str): The name of the drug to search for.
    
    Returns:
        tuple: A Plotly figure and a formatted string with the top serious outcomes.
    """
    data = get_serious_outcomes(drug_name)
    chart = create_outcome_chart(data, drug_name)
    text_summary = format_serious_outcomes_results(data, drug_name)
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

def time_series_tool(drug_name: str, event_name: str, aggregation: str):
    """
    MCP Tool: Creates a time-series plot for a drug-event pair.

    Args:
        drug_name (str): The name of the drug.
        event_name (str): The name of the adverse event.
        aggregation (str): Time aggregation ('Yearly' or 'Quarterly').

    Returns:
        A Plotly figure.
    """
    agg_code = 'Y' if aggregation == 'Yearly' else 'Q'
    data = get_time_series_data(drug_name, event_name)
    chart = create_time_series_chart(data, drug_name, event_name, time_aggregation=agg_code)
    return chart

def report_source_tool(drug_name: str):
    """
    MCP Tool: Creates a pie chart of report sources for a given drug.

    Args:
        drug_name (str): The name of the drug.

    Returns:
        A Plotly figure.
    """
    data = get_report_source_data(drug_name)
    chart = create_pie_chart(data, drug_name)
    return chart

# --- Gradio Interface ---

interface1 = gr.Interface(
    fn=top_adverse_events_tool,
    inputs=[
        gr.Textbox(
            label="Drug Name", 
            info="Enter a brand or generic drug name (e.g., 'Aspirin', 'Lisinopril')."
        ),
        gr.Radio(
            ["All", "Male", "Female"], 
            label="Patient Sex", 
            value="All"
        ),
        gr.Slider(
            0, 120, 
            value=0, 
            label="Minimum Age", 
            step=1
        ),
        gr.Slider(
            0, 120, 
            value=120, 
            label="Maximum Age", 
            step=1
        ),
    ],
    outputs=[
        gr.Plot(label="Top Adverse Events Chart"),
        gr.Textbox(label="Top Adverse Events (Raw Data)", lines=15)
    ],
    title="Top Adverse Events by Drug",
    description="Find the most frequently reported adverse events for a specific medication.",
    examples=[["Lisinopril"], ["Ozempic"], ["Metformin"]],
)

interface3 = gr.Interface(
    fn=serious_outcomes_tool,
    inputs=[
        gr.Textbox(
            label="Drug Name", 
            info="Enter a brand or generic drug name (e.g., 'Aspirin', 'Lisinopril')."
        )
    ],
    outputs=[
        gr.Plot(label="Top Serious Outcomes Chart"),
        gr.Textbox(label="Top Serious Outcomes (Raw Data)", lines=15)
    ],
    title="Serious Outcome Analysis",
    description="Find the most frequently reported serious outcomes (e.g., hospitalization, death) for a specific medication.",
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

interface4 = gr.Interface(
    fn=time_series_tool,
    inputs=[
        gr.Textbox(label="Drug Name", info="e.g., 'Ibuprofen'"),
        gr.Textbox(label="Adverse Event", info="e.g., 'Headache'"),
        gr.Radio(["Yearly", "Quarterly"], label="Aggregation", value="Yearly")
    ],
    outputs=[gr.Plot(label="Report Trends")],
    title="Time-Series Trend Plotting",
    description="Plot the number of adverse event reports over time for a specific drug-event pair.",
    examples=[["Lisinopril", "Cough", "Yearly"], ["Ozempic", "Nausea", "Quarterly"]],
)

interface5 = gr.Interface(
    fn=report_source_tool,
    inputs=[
        gr.Textbox(label="Drug Name", info="e.g., 'Aspirin', 'Lisinopril'")
    ],
    outputs=[gr.Plot(label="Report Source Breakdown")],
    title="Report Source Breakdown",
    description="Show a pie chart breaking down the source of the reports (e.g., Consumer, Physician).",
    examples=[["Lisinopril"], ["Ozempic"]],
)

demo = gr.TabbedInterface(
    [interface1, interface3, interface2, interface4, interface5], 
    ["Top Events", "Serious Outcomes", "Event Frequency", "Time-Series Trends", "Report Sources"],
    title="Medication Adverse-Event Explorer"
)

if __name__ == "__main__":
    demo.launch(mcp_server=True, server_name="0.0.0.0") 