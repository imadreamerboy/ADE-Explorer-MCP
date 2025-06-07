import requests
from cachetools import TTLCache, cached
import time
from typing import Optional, Tuple

API_BASE_URL = "https://api.fda.gov/drug/event.json"
# Cache with a TTL of 10 minutes (600 seconds)
cache = TTLCache(maxsize=256, ttl=600)

# 240 requests per minute per IP. A 0.25s delay is a simple way to stay under.
REQUEST_DELAY_SECONDS = 0.25

DRUG_SYNONYM_MAPPING = {
    "tylenol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "aleve": "naproxen",
    "benadryl": "diphenhydramine",
    "claritin": "loratadine",
    "zyrtec": "cetirizine",
    "allegra": "fexofenadine",
    "zantac": "ranitidine",
    "pepcid": "famotidine",
    "prilosec": "omeprazole",
    "lipitor": "atorvastatin",
    "zocor": "simvastatin",
    "norvasc": "amlodipine",
    "hydrochlorothiazide": "hctz",
    "glucophage": "metformin",
    "synthroid": "levothyroxine",
    "ambien": "zolpidem",
    "xanax": "alprazolam",
    "prozac": "fluoxetine",
    "zoloft": "sertraline",
    "paxil": "paroxetine",
    "lexapro": "escitalopram",
    "cymbalta": "duloxetine",
    "wellbutrin": "bupropion",
    "desyrel": "trazodone",
    "eliquis": "apixaban",
    "xarelto": "rivaroxaban",
    "pradaxa": "dabigatran",
    "coumadin": "warfarin",
    "januvia": "sitagliptin",
    "tradjenta": "linagliptin",
    "jardiance": "empagliflozin",
    "farxiga": "dapagliflozin",
    "invokana": "canagliflozin",
    "ozempic": "semaglutide",
    "victoza": "liraglutide",
    "trulicity": "dulaglutide",
    "humira": "adalimumab",
    "enbrel": "etanercept",
    "remicade": "infliximab",
    "stelara": "ustekinumab",
    "keytruda": "pembrolizumab",
    "opdivo": "nivolumab",
    "revlimid": "lenalidomide",
    "rituxan": "rituximab",
    "herceptin": "trastuzumab",
    "avastin": "bevacizumab",
    "spiriva": "tiotropium",
    "advair": "fluticasone/salmeterol",
    "symbicort": "budesonide/formoterol",
    "singulair": "montelukast",
    "lyrica": "pregabalin",
    "neurontin": "gabapentin",
    "topamax": "topiramate",
    "lamictal": "lamotrigine",
    "keppra": "levetiracetam",
    "dilantin": "phenytoin",
    "tegretol": "carbamazepine",
    "depakote": "divalproex",
    "vyvanse": "lisdexamfetamine",
    "adderall": "amphetamine/dextroamphetamine",
    "ritalin": "methylphenidate",
    "concerta": "methylphenidate",
    "focalin": "dexmethylphenidate",
    "strattera": "atomoxetine",
    "viagra": "sildenafil",
    "cialis": "tadalafil",
    "levitra": "vardenafil",
    "bactrim": "sulfamethoxazole/trimethoprim",
    "keflex": "cephalexin",
    "augmentin": "amoxicillin/clavulanate",
    "zithromax": "azithromycin",
    "levaquin": "levofloxacin",
    "cipro": "ciprofloxacin",
    "diflucan": "fluconazole",
    "tamiflu": "oseltamivir",
    "valtrex": "valacyclovir",
    "zofran": "ondansetron",
    "phenergan": "promethazine",
    "imitrex": "sumatriptan",
    "flexeril": "cyclobenzaprine",
    "soma": "carisoprodol",
    "valium": "diazepam",
    "ativan": "lorazepam",
    "klonopin": "clonazepam",
    "restoril": "temazepam",
    "ultram": "tramadol",
    "percocet": "oxycodone/acetaminophen",
    "vicodin": "hydrocodone/acetaminophen",
    "oxycontin": "oxycodone",
    "dilaudid": "hydromorphone",
    "morphine": "ms contin",
    "fentanyl": "duragesic"
}

OUTCOME_MAPPING = {
    "1": "Recovered/Resolved",
    "2": "Recovering/Resolving",
    "3": "Not Recovered/Not Resolved",
    "4": "Recovered/Resolved with Sequelae",
    "5": "Fatal",
    "6": "Unknown",
}

QUALIFICATION_MAPPING = {
    "1": "Physician",
    "2": "Pharmacist",
    "3": "Other Health Professional",
    "4": "Lawyer",
    "5": "Consumer or Non-Health Professional",
}

SERIOUS_OUTCOME_FIELDS = [
    "seriousnessdeath",
    "seriousnesslifethreatening",
    "seriousnesshospitalization",
    "seriousnessdisabling",
    "seriousnesscongenitalanomali",
    "seriousnessother",
]

def get_top_adverse_events(drug_name: str, limit: int = 10, patient_sex: Optional[str] = None, age_range: Optional[Tuple[int, int]] = None) -> dict:
    """
    Query OpenFDA to get the top adverse events for a given drug.

    Args:
        drug_name (str): The name of the drug to search for (brand or generic).
        limit (int): The maximum number of adverse events to return.
        patient_sex (str): The patient's sex to filter by ('1' for Male, '2' for Female).
        age_range (tuple): A tuple containing min and max age, e.g., (20, 50).

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)

    # Build the search query
    search_terms = [f'patient.drug.medicinalproduct:"{drug_name_processed}"']
    if patient_sex and patient_sex in ["1", "2"]:
        search_terms.append(f'patient.patientsex:"{patient_sex}"')
    if age_range and len(age_range) == 2:
        min_age, max_age = age_range
        search_terms.append(f'patient.patientonsetage:[{min_age} TO {max_age}]')

    search_query = "+AND+".join(search_terms)

    # Using a simple cache key that includes filters
    cache_key = f"top_events_{drug_name_processed}_{limit}_{patient_sex}_{age_range}"

    if cache_key in cache:
        return cache[cache_key]

    # Query for top events by count
    count_query_url = (
        f'{API_BASE_URL}?search={search_query}'
        f'&count=patient.reaction.reactionmeddrapt.exact&limit={limit}'
    )
    
    try:
        # Respect rate limits
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(count_query_url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        # Query for total reports matching the filters
        total_query_url = f'{API_BASE_URL}?search={search_query}'
        time.sleep(REQUEST_DELAY_SECONDS)
        total_response = requests.get(total_query_url)
        total_response.raise_for_status()
        total_data = total_response.json()
        total_reports = total_data.get("meta", {},).get("results", {}).get("total", 0)

        # Add total to the main data object
        if 'meta' not in data:
            data['meta'] = {}
        data['meta']['total_reports_for_query'] = total_reports
                
        cache[cache_key] = data
        return data

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"No data found for '{drug_name}' with the specified filters. The drug may not be in the database, or there may be no reports matching the filter criteria."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network request error occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_drug_event_pair_frequency(drug_name: str, event_name: str) -> dict:
    """
    Query OpenFDA to get the total number of reports for a specific
    drug-adverse event pair, and the total reports for the drug alone.

    Args:
        drug_name (str): The name of the drug.
        event_name (str): The name of the adverse event.

    Returns:
        dict: A dictionary containing the results or an error message.
              Includes `total` (for the pair) and `total_for_drug`.
    """
    if not drug_name or not event_name:
        return {"error": "Drug name and event name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)
    event_name_processed = event_name.lower().strip()

    cache_key = f"pair_freq_{drug_name_processed}_{event_name_processed}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # First, get total reports for the drug to see if it exists
        drug_query = f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        time.sleep(REQUEST_DELAY_SECONDS)
        drug_response = requests.get(f"{API_BASE_URL}?{drug_query}")
        
        # This is a critical failure if the drug isn't found
        drug_response.raise_for_status() 
        
        drug_data = drug_response.json()
        total_for_drug = drug_data.get("meta", {}).get("results", {}).get("total", 0)

        # Second, get reports for the specific drug-event pair
        pair_query = (
            f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
            f'+AND+patient.reaction.reactionmeddrapt:"{event_name_processed}"'
        )
        time.sleep(REQUEST_DELAY_SECONDS)
        pair_response = requests.get(f"{API_BASE_URL}?{pair_query}")
        
        total_for_pair = 0
        if pair_response.status_code == 200:
            pair_data = pair_response.json()
            total_for_pair = pair_data.get("meta", {}).get("results", {}).get("total", 0)
        # We don't raise for 404 on the pair, as it just means 0 results
        elif pair_response.status_code != 404:
            pair_response.raise_for_status()

        # Construct a consistent response structure
        data = {
            "meta": {
                "results": {
                    "total": total_for_pair,
                    "total_for_drug": total_for_drug
                }
            }
        }
        
        cache[cache_key] = data
        return data

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return {"error": f"No data found for drug '{drug_name}'. It may be misspelled or not in the database."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network request error occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_serious_outcomes(drug_name: str, limit: int = 6) -> dict:
    """
    Query OpenFDA to get the most frequent serious outcomes for a given drug.
    This function makes multiple API calls to count different outcome fields.

    Args:
        drug_name (str): The name of the drug to search for.
        limit (int): The maximum number of outcomes to return.

    Returns:
        dict: A dictionary containing aggregated results or an error.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)
    
    # Use a cache key for the aggregated result
    cache_key = f"serious_outcomes_aggregated_{drug_name_processed}_{limit}"
    if cache_key in cache:
        return cache[cache_key]

    aggregated_results = {}
    
    # Base search for all serious reports
    base_search_query = f'patient.drug.medicinalproduct:"{drug_name_processed}"+AND+serious:1'

    # Get total number of serious reports
    total_serious_reports = 0
    try:
        total_query_url = f"{API_BASE_URL}?search={base_search_query}"
        time.sleep(REQUEST_DELAY_SECONDS)
        response = requests.get(total_query_url)
        if response.status_code == 200:
            total_data = response.json()
            total_serious_reports = total_data.get("meta", {}).get("results", {}).get("total", 0)
        elif response.status_code != 404:
            # If this call fails, we can still proceed, the total will just be 0.
            pass
    except requests.exceptions.RequestException:
        # If fetching total fails, proceed without it.
        pass

    for field in SERIOUS_OUTCOME_FIELDS:
        try:
            # Each query counts reports where the specific seriousness field exists
            query = f"search={base_search_query}+AND+_exists_:{field}"
            
            time.sleep(REQUEST_DELAY_SECONDS)
            response = requests.get(f"{API_BASE_URL}?{query}")
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get("meta", {}).get("results", {}).get("total", 0)
                if total_count > 0:
                    # Use a more readable name for the outcome
                    outcome_name = field.replace("seriousness", "").replace("anomali", "anomaly").title()
                    aggregated_results[outcome_name] = total_count
            # Ignore 404s, as they just mean no results for that specific outcome
            elif response.status_code != 404:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            return {"error": f"A network request error occurred for field {field}: {e}"}

    if not aggregated_results:
        return {"error": f"No serious outcome data found for drug: '{drug_name}'."}

    # Format the results to match the expected structure for plotting
    final_data = {
        "results": [{"term": k, "count": v} for k, v in aggregated_results.items()],
        "meta": {"total_reports_for_query": total_serious_reports}
    }
    
    # Sort results by count, descending, and then limit
    final_data["results"] = sorted(final_data["results"], key=lambda x: x['count'], reverse=True)
    if limit:
        final_data["results"] = final_data["results"][:limit]
    
    cache[cache_key] = final_data
    return final_data

def get_time_series_data(drug_name: str, event_name: str) -> dict:
    """
    Query OpenFDA to get the time series data for a drug-event pair.

    Args:
        drug_name (str): The name of the drug.
        event_name (str): The name of the adverse event.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name or not event_name:
        return {"error": "Drug name and event name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)
    event_name_processed = event_name.lower().strip()

    cache_key = f"time_series_{drug_name_processed}_{event_name_processed}"
    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'+AND+patient.reaction.reactionmeddrapt:"{event_name_processed}"'
        f'&count=receiptdate'
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

def get_report_source_data(drug_name: str, limit: int = 5) -> dict:
    """
    Query OpenFDA to get the breakdown of report sources for a given drug.

    Args:
        drug_name (str): The name of the drug to search for.
        limit (int): The maximum number of sources to return.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)

    cache_key = f"report_source_{drug_name_processed}_{limit}"
    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'&count=primarysource.qualification'
    )

    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()
        
        data = response.json()

        # Translate the qualification codes and calculate total before limiting
        if "results" in data:
            # Sort by count first
            data['results'] = sorted(data['results'], key=lambda x: x['count'], reverse=True)

            # Calculate total from all results before limiting
            total_with_source = sum(item['count'] for item in data['results'])
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['total_reports_for_query'] = total_with_source
            
            # Translate codes after processing
            for item in data["results"]:
                term_str = str(item["term"])
                item["term"] = QUALIFICATION_MAPPING.get(term_str, f"Unknown ({term_str})")

            # Apply limit
            if limit:
                data['results'] = data['results'][:limit]

        cache[cache_key] = data
        return data

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"No data found for drug: '{drug_name}'."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network request error occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"} 