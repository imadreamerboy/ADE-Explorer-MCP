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
    create_pie_chart,
    create_placeholder_chart
)
import pandas as pd

# --- Formatting Functions ---

def format_pair_frequency_results(data: dict, drug_name: str, event_name: str) -> str:
    """Formats the results for the drug-event pair frequency tool."""
    if "error" in data:
        return f"An error occurred: {data['error']}"
    
    results = data.get("meta", {}).get("results", {})
    total_reports = results.get("total", 0)
    total_for_drug = results.get("total_for_drug", 0)

    percentage_string = ""
    if total_for_drug > 0:
        percentage = (total_reports / total_for_drug) * 100
        percentage_string = (
            f"\n\nThis combination accounts for **{percentage:.2f}%** of the **{total_for_drug:,}** "
            f"total adverse event reports for '{drug_name.title()}' in the database."
        )

    result = (
        f"Found **{total_reports:,}** reports for the combination of "
        f"'{drug_name.title()}' and '{event_name.title()}'.{percentage_string}\n\n"
        "**Source**: FDA FAERS via OpenFDA\n"
        "**Disclaimer**: Spontaneous reports do not prove causation. Consult a healthcare professional."
    )
    return result

# --- Tool Functions ---

def top_adverse_events_tool(drug_name: str, top_n: int = 10, patient_sex: str = "all", min_age: int = 0, max_age: int = 120):
    """
    MCP Tool: Finds the top reported adverse events for a given drug.

    Args:
        drug_name (str): The generic name of the drug is preferred! A small sample of brand names (e.g., 'Tylenol') are converted to generic names for demonstration purposes.
        top_n (int): The number of top adverse events to return.
        patient_sex (str): The patient's sex to filter by.
        min_age (int): The minimum age for the filter.
        max_age (int): The maximum age for the filter.
    
    Returns:
        tuple: A Plotly figure, a Pandas DataFrame, and a summary string.
    """
    if top_n is None:
        top_n = 10
    if patient_sex is None:
        patient_sex = "all"
    if min_age is None:
        min_age = 0
    if max_age is None:
        max_age = 120

    sex_code = None
    if patient_sex == "Male":
        sex_code = "1"
    elif patient_sex == "Female":
        sex_code = "2"
    
    age_range = None
    if min_age > 0 or max_age < 120:
        age_range = (min_age, max_age)

    data = get_top_adverse_events(drug_name, limit=top_n, patient_sex=sex_code, age_range=age_range)
    
    if "error" in data:
        error_message = f"An error occurred: {data['error']}"
        return create_placeholder_chart(error_message), pd.DataFrame(), error_message
    
    if "results" not in data or not data["results"]:
        message = f"No adverse event data found for '{drug_name}'. The drug may not be in the database or it might be misspelled."
        return create_placeholder_chart(message), pd.DataFrame(), message
        
    chart = create_bar_chart(data, drug_name)
    
    df = pd.DataFrame(data["results"])
    df = df.rename(columns={"term": "Adverse Event", "count": "Report Count"})
    
    total_reports = data.get("meta", {}).get("total_reports_for_query", 0)
    if total_reports > 0:
        df['Relative Frequency (%)'] = ((df['Report Count'] / total_reports) * 100).round(2)
    else:
        df['Relative Frequency (%)'] = 0.0

    header = (
        f"### Top {len(df)} Adverse Events for '{drug_name.title()}'\n"
        f"Based on **{total_reports:,}** total reports matching the given filters.\n"
        "**Source**: FDA FAERS via OpenFDA\n"
        "**Disclaimer**: Spontaneous reports do not prove causation. Consult a healthcare professional."
    )
    return chart, df, header

def serious_outcomes_tool(drug_name: str, top_n: int = 6):
    """
    MCP Tool: Finds the top reported serious outcomes for a given drug.

    Args:
        drug_name (str): The generic name of the drug is preferred. A small sample of brand names (e.g., 'Tylenol') are converted to generic names for demonstration purposes.
        top_n (int): The number of top serious outcomes to return.
    
    Returns:
        tuple: A Plotly figure, a Pandas DataFrame, and a summary string.
    """
    if top_n is None:
        top_n = 6
    data = get_serious_outcomes(drug_name, limit=top_n)

    if "error" in data:
        error_message = f"An error occurred: {data['error']}"
        return create_placeholder_chart(error_message), pd.DataFrame(), error_message

    if "results" not in data or not data["results"]:
        message = f"No serious outcome data found for '{drug_name}'. The drug may not be in the database or it might be misspelled."
        return create_placeholder_chart(message), pd.DataFrame(), message

    chart = create_outcome_chart(data, drug_name)

    df = pd.DataFrame(data["results"])
    df = df.rename(columns={"term": "Serious Outcome", "count": "Report Count"})
    
    total_serious_reports = data.get("meta", {}).get("total_reports_for_query", 0)
    if total_serious_reports > 0:
        df['% of Serious Reports'] = ((df['Report Count'] / total_serious_reports) * 100).round(2)
    else:
        df['% of Serious Reports'] = 0.0

    header = (
        f"### Top {len(df)} Serious Outcomes for '{drug_name.title()}'\n"
        f"Out of **{total_serious_reports:,}** total serious reports. "
        "Note: a single report may be associated with multiple outcomes.\n"
        "**Source**: FDA FAERS via OpenFDA\n"
        "**Disclaimer**: Spontaneous reports do not prove causation. Consult a healthcare professional."
    )
    return chart, df, header

def drug_event_stats_tool(drug_name: str, event_name: str):
    """
    MCP Tool: Gets the total number of reports for a specific drug and adverse event pair.

    Args:
        drug_name (str): The generic name of the drug is preferred. A small sample of brand names (e.g., 'Tylenol') are converted to generic names for demonstration purposes.
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
        drug_name (str): The generic name of the drug is preferred. A small sample of brand names (e.g., 'Tylenol') are converted to generic names for demonstration purposes.
        event_name (str): The name of the adverse event.
        aggregation (str): Time aggregation ('Yearly' or 'Quarterly').

    Returns:
        A Plotly figure.
    """
    agg_code = 'Y' if aggregation == 'Yearly' else 'Q'
    data = get_time_series_data(drug_name, event_name)
    
    if "error" in data or not data.get("results"):
        return create_placeholder_chart(f"No time-series data found for '{drug_name}' and '{event_name}'.")

    chart = create_time_series_chart(data, drug_name, event_name, time_aggregation=agg_code)
    return chart

def report_source_tool(drug_name: str, top_n: int = 5):
    """
    MCP Tool: Creates a pie chart of report sources for a given drug.

    Args:
        drug_name (str): The generic name of the drug is preferred. A small sample of brand names (e.g., 'Tylenol') are converted to generic names for demonstration purposes.
        top_n (int): The number of top sources to return.

    Returns:
        tuple: A Plotly figure, a Pandas DataFrame, and a summary string.
    """
    if top_n is None:
        top_n = 5
    data = get_report_source_data(drug_name, limit=top_n)

    if "error" in data:
        error_message = f"An error occurred: {data['error']}"
        return create_placeholder_chart(error_message), pd.DataFrame(), error_message

    if not data or not data.get("results"):
        message = f"No report source data found for '{drug_name}'."
        return create_placeholder_chart(message), pd.DataFrame(), message

    chart = create_pie_chart(data, drug_name)
    
    df = pd.DataFrame(data['results'])
    df = df.rename(columns={"term": "Source", "count": "Report Count"})

    total_reports = data.get("meta", {}).get("total_reports_for_query", 0)
    if total_reports > 0:
        df['Percentage'] = ((df['Report Count'] / total_reports) * 100).round(2)
    else:
        df['Percentage'] = 0.0

    header = (
        f"### Report Sources for '{drug_name.title()}'\n"
        f"Based on **{total_reports:,}** reports with source information."
    )
    return chart, df, header

# --- Gradio Interface ---

with open("gradio_readme.md", "r") as f:
    readme_content = f.read()

with gr.Blocks(title="Medication Adverse-Event Explorer") as demo:
    gr.Markdown("# Medication Adverse-Event Explorer")

    with gr.Tabs():
        with gr.TabItem("About"):
            gr.Markdown(readme_content)

        with gr.TabItem("Top Events"):
            gr.Interface(
                fn=top_adverse_events_tool,
                inputs=[
                    gr.Textbox(
                        label="Drug Name", 
                        info="Enter a brand or generic drug name (e.g., 'Aspirin', 'Lisinopril')."
                    ),
                    gr.Slider(
                        5, 50, 
                        value=10, 
                        label="Number of Events to Show", 
                        step=1
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
                    gr.DataFrame(label="Top Adverse Events", interactive=False),
                    gr.Markdown()
                ],
                title="Top Adverse Events by Drug",
                description="Find the most frequently reported adverse events for a specific medication.",
                examples=[["Lisinopril"], ["Ozempic"], ["Metformin"]],
                allow_flagging="never",
            )

        with gr.TabItem("Serious Outcomes"):
            gr.Interface(
                fn=serious_outcomes_tool,
                inputs=[
                    gr.Textbox(
                        label="Drug Name", 
                        info="Enter a brand or generic drug name (e.g., 'Aspirin', 'Lisinopril')."
                    ),
                    gr.Slider(1, 6, value=6, label="Number of Outcomes to Show", step=1),
                ],
                outputs=[
                    gr.Plot(label="Top Serious Outcomes Chart"),
                    gr.DataFrame(label="Top Serious Outcomes", interactive=False),
                    gr.Markdown()
                ],
                title="Serious Outcome Analysis",
                description="Find the most frequently reported serious outcomes (e.g., hospitalization, death) for a specific medication.",
                examples=[["Lisinopril"], ["Ozempic"], ["Metformin"]],
                allow_flagging="never",
            )

        with gr.TabItem("Event Frequency"):
            gr.Interface(
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

        with gr.TabItem("Time-Series Trends"):
            gr.Interface(
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

        with gr.TabItem("Report Sources"):
            gr.Interface(
                fn=report_source_tool,
                inputs=[
                    gr.Textbox(label="Drug Name", info="e.g., 'Aspirin', 'Lisinopril'"),
                    gr.Slider(1, 5, value=5, label="Number of Sources to Show", step=1),
                ],
                outputs=[
                    gr.Plot(label="Report Source Breakdown"),
                    gr.DataFrame(label="Report Source Data", interactive=False),
                    gr.Markdown()
                ],
                title="Report Source Breakdown",
                description="Show a pie chart breaking down the source of the reports (e.g., Consumer, Physician).",
                examples=[["Lisinopril"], ["Ibuprofen"]],
                allow_flagging="never",
            )

if __name__ == "__main__":
    demo.launch(mcp_server=True, server_name="0.0.0.0") 