# Medication Adverse-Event Explorer

Welcome to the Medication Adverse-Event Explorer, an interactive tool for exploring data from the FDA Adverse Event Reporting System (FAERS).

<iframe width="560" height="315" src="https://www.youtube.com/embed/noGG-lQwn2U" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

***

### About This Tool

This application provides a user-friendly interface to query and visualize data on adverse events reported for various medications. It is designed to help researchers, healthcare professionals, and the public explore trends and patterns in post-market drug safety data. It also functions as an MCP (Machine-Composable Protocol) server, allowing it to be used as a tool by language models.

### Data Source

All data is sourced directly from the **[openFDA](https://open.fda.gov/)** API, which provides public access to the FAERS database. This database contains information on adverse event and medication error reports submitted to the FDA.

### Disclaimer

**This tool is for informational and research purposes only and is not a substitute for professional medical advice.** The data presented here is based on spontaneous reports, which have not been scientifically verified and do not prove causation. Always consult a qualified healthcare professional for any medical concerns or before making any decisions about your treatment.

***

### How to Use the Tabs

The explorer is organized into several tabs, each providing a different view of the data:

-   **Top Events:** Find the most frequently reported adverse events for a specific drug. You can filter the results by patient sex and age range.
-   **Serious Outcomes:** See a breakdown of the most serious outcomes (e.g., hospitalization, death) reported for a drug.
-   **Event Frequency:** Get the total number of reports for a specific combination of a drug and an adverse event.
-   **Time-Series Trends:** Plot the number of adverse event reports over time for a specific drug and event pair.
-   **Report Sources:** View a pie chart showing the breakdown of who reported the adverse events (e.g., Consumer, Physician, Pharmacist).

**A Note on Drug Names:** For demonstration purposes, a small number of common brand names (e.g., 'Tylenol') are automatically converted to their generic equivalents (e.g., 'acetaminophen'). For the most accurate results, it is always best to use the generic name of a drug. 