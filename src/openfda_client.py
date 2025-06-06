import requests
from cachetools import TTLCache, cached
import time

API_BASE_URL = "https://api.fda.gov/drug/event.json"
# Cache with a TTL of 10 minutes (600 seconds)
cache = TTLCache(maxsize=256, ttl=600)

# 240 requests per minute per IP. A 0.25s delay is a simple way to stay under.
REQUEST_DELAY_SECONDS = 0.25

def get_top_adverse_events(drug_name: str, limit: int = 10) -> dict:
    """
    Query OpenFDA to get the top adverse events for a given drug.

    Args:
        drug_name (str): The name of the drug to search for (brand or generic).
        limit (int): The maximum number of adverse events to return.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()

    # Using a simple cache key
    cache_key = f"top_events_{drug_name_processed}_{limit}"

    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'&count=patient.reaction.reactionmeddrapt.exact&limit={limit}'
    )
    
    try:
        # Respect rate limits
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        cache[cache_key] = data
        return data

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"No data found for drug: '{drug_name}'. It might be misspelled or not in the database."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network request error occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_drug_event_pair_frequency(drug_name: str, event_name: str) -> dict:
    """
    Query OpenFDA to get the total number of reports for a specific
    drug-adverse event pair.

    Args:
        drug_name (str): The name of the drug.
        event_name (str): The name of the adverse event.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name or not event_name:
        return {"error": "Drug name and event name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    event_name_processed = event_name.lower().strip()

    cache_key = f"pair_freq_{drug_name_processed}_{event_name_processed}"
    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'+AND+patient.reaction.reactionmeddrapt:"{event_name_processed}"'
    )

    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()
        
        data = response.json()
        cache[cache_key] = data
        return data

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"No data found for drug '{drug_name}' and event '{event_name}'. They may be misspelled or not in the database."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network request error occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
