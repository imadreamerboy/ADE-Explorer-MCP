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