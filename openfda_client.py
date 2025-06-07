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

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'&count=patient.reaction.reactionoutcome.exact&limit={limit}'
    )
    
    try:
        # Respect rate limits
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        # Translate the outcome codes to human-readable terms
        if "results" in data:
            for item in data["results"]:
                item["term"] = OUTCOME_MAPPING.get(item["term"], f"Unknown ({item['term']})")

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
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)
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

def get_serious_outcomes(drug_name: str, limit: int = 10) -> dict:
    """
    Query OpenFDA to get the most frequent serious outcomes for a given drug.
    Outcomes include: death, disability, hospitalization, etc.

    Args:
        drug_name (str): The name of the drug to search for.
        limit (int): The maximum number of outcomes to return.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)
    cache_key = f"serious_outcomes_{drug_name_processed}_{limit}"

    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'&count=reactionoutcome.exact&limit={limit}'
    )

    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()
        
        data = response.json()
        
        # Map outcome codes to human-readable names
        if "results" in data:
            for item in data["results"]:
                item["term"] = OUTCOME_MAPPING.get(item["term"], f"Unknown ({item['term']})")
        
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

def get_report_source_data(drug_name: str) -> dict:
    """
    Query OpenFDA to get the breakdown of report sources for a given drug.

    Args:
        drug_name (str): The name of the drug to search for.

    Returns:
        dict: The JSON response from the API, or an error dictionary.
    """
    if not drug_name:
        return {"error": "Drug name cannot be empty."}

    drug_name_processed = drug_name.lower().strip()
    drug_name_processed = DRUG_SYNONYM_MAPPING.get(drug_name_processed, drug_name_processed)

    cache_key = f"report_source_{drug_name_processed}"
    if cache_key in cache:
        return cache[cache_key]

    query = (
        f'search=patient.drug.medicinalproduct:"{drug_name_processed}"'
        f'&count=primarysource.qualification.exact&limit=5'
    )

    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        
        response = requests.get(f"{API_BASE_URL}?{query}")
        response.raise_for_status()
        
        data = response.json()

        # Translate the qualification codes to human-readable terms
        if "results" in data:
            for item in data["results"]:
                item["term"] = QUALIFICATION_MAPPING.get(item["term"], f"Unknown ({item['term']})")

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