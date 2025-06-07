import plotly.graph_objects as go
import pandas as pd

def create_bar_chart(data: dict, drug_name: str):
    """
    Creates a Plotly bar chart from the OpenFDA data.

    Args:
        data (dict): The data from the OpenFDA client.
        drug_name (str): The name of the drug.

    Returns:
        A Plotly Figure object if data is valid, otherwise None.
    """
    if "error" in data or "results" not in data or not data["results"]:
        return None

    try:
        df = pd.DataFrame(data["results"])
        df = df.rename(columns={"term": "Adverse Event", "count": "Report Count"})
        
        # Ensure 'Report Count' is numeric
        df['Report Count'] = pd.to_numeric(df['Report Count'])

        # Sort for better visualization
        df = df.sort_values(by="Report Count", ascending=True)

        fig = go.Figure(
            go.Bar(
                x=df["Report Count"],
                y=df["Adverse Event"],
                orientation='h',
                marker=dict(color='skyblue')
            )
        )

        fig.update_layout(
            title_text=f"Top Reported Adverse Events for {drug_name.title()}",
            xaxis_title="Number of Reports",
            yaxis_title="Adverse Event",
            yaxis=dict(automargin=True),
            height=max(400, len(df) * 30) # Dynamically adjust height
        )

        return fig
    except Exception:
        return None

def create_outcome_chart(data: dict, drug_name: str):
    """
    Creates a Plotly bar chart for serious outcomes from OpenFDA data.

    Args:
        data (dict): The data from the OpenFDA client.
        drug_name (str): The name of the drug.

    Returns:
        A Plotly Figure object if data is valid, otherwise None.
    """
    if "error" in data or "results" not in data or not data["results"]:
        return None

    try:
        df = pd.DataFrame(data["results"])
        df = df.rename(columns={"term": "Serious Outcome", "count": "Report Count"})
        
        df['Report Count'] = pd.to_numeric(df['Report Count'])
        df = df.sort_values(by="Report Count", ascending=True)

        fig = go.Figure(
            go.Bar(
                x=df["Report Count"],
                y=df["Serious Outcome"],
                orientation='h',
                marker=dict(color='crimson') # Different color for distinction
            )
        )

        fig.update_layout(
            title_text=f"Top Serious Outcomes for {drug_name.title()}",
            xaxis_title="Number of Reports",
            yaxis_title="Serious Outcome",
            yaxis=dict(automargin=True),
            height=max(400, len(df) * 40)
        )

        return fig
    except Exception:
        return None

def create_time_series_chart(data: dict, drug_name: str, event_name: str, time_aggregation: str = 'Y'):
    """
    Creates a Plotly time-series chart from OpenFDA data.

    Args:
        data (dict): The data from the OpenFDA client.
        drug_name (str): The name of the drug.
        event_name (str): The name of the adverse event.
        time_aggregation (str): The time unit for aggregation ('Y' for year, 'Q' for quarter).

    Returns:
        A Plotly Figure object if data is valid, otherwise None.
    """
    if "error" in data or "results" not in data or not data["results"]:
        return None

    try:
        df = pd.DataFrame(data["results"])
        df['time'] = pd.to_datetime(df['time'], format='%Y%m%d')
        
        # Resample data
        df = df.set_index('time').resample(time_aggregation)['count'].sum().reset_index()
        
        aggregation_label = "Year" if time_aggregation == 'Y' else "Quarter"

        fig = go.Figure(
            go.Scatter(
                x=df["time"],
                y=df["count"],
                mode='lines+markers',
                line=dict(color='royalblue'),
            )
        )

        fig.update_layout(
            title_text=f"Report Trend for {drug_name.title()} and {event_name.title()}",
            xaxis_title=f"Report {aggregation_label}",
            yaxis_title="Number of Reports",
            yaxis=dict(automargin=True),
        )

        return fig
    except Exception as e:
        print(f"Error creating time-series chart: {e}")
        return None

def create_pie_chart(data: dict, drug_name: str):
    """
    Creates a Plotly pie chart for report source breakdown.

    Args:
        data (dict): The data from the OpenFDA client.
        drug_name (str): The name of the drug.

    Returns:
        A Plotly Figure object if data is valid, otherwise None.
    """
    if "error" in data or "results" not in data or not data["results"]:
        return None

    try:
        df = pd.DataFrame(data["results"])
        df = df.rename(columns={"term": "Source", "count": "Count"})

        fig = go.Figure(
            go.Pie(
                labels=df["Source"],
                values=df["Count"],
                hole=.3,
                pull=[0.05] * len(df) # Explode slices slightly
            )
        )

        fig.update_layout(
            title_text=f"Report Sources for {drug_name.title()}",
            showlegend=True
        )

        return fig
    except Exception as e:
        print(f"Error creating pie chart: {e}")
        return None 