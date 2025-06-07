import pytest
from unittest.mock import patch, MagicMock
import requests
from openfda_client import get_top_adverse_events, get_drug_event_pair_frequency, cache

@pytest.fixture(autouse=True)
def clear_cache():
    """Fixture to clear the cache before each test."""
    cache.clear()

def mock_response(status_code=200, json_data=None, raise_for_status=None):
    """Helper function to create a mock response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    return mock_resp

@patch('requests.get')
def test_get_top_adverse_events_success(mock_get):
    """Test successful API call for top adverse events."""
    mock_json = {"results": [{"term": "Nausea", "count": 100}]}
    mock_get.return_value = mock_response(json_data=mock_json)
    
    result = get_top_adverse_events("testdrug")
    
    assert result == mock_json
    mock_get.assert_called_once()

@patch('requests.get')
def test_get_top_adverse_events_404(mock_get):
    """Test 404 Not Found error for top adverse events."""
    http_error = requests.exceptions.HTTPError("404 Client Error")
    mock_get.return_value = mock_response(status_code=404, raise_for_status=http_error)
    
    result = get_top_adverse_events("nonexistentdrug")
    
    assert "error" in result
    assert "No data found" in result["error"]

@patch('requests.get')
def test_get_drug_event_pair_frequency_success(mock_get):
    """Test successful API call for drug-event pair frequency."""
    mock_json = {"meta": {"results": {"total": 50}}}
    mock_get.return_value = mock_response(json_data=mock_json)
    
    result = get_drug_event_pair_frequency("testdrug", "testevent")
    
    assert result == mock_json
    mock_get.assert_called_once()

def test_empty_drug_name_returns_error():
    """Test that empty inputs are handled correctly without calling the API."""
    result = get_top_adverse_events("")
    assert "error" in result
    
    result2 = get_drug_event_pair_frequency("", "testevent")
    assert "error" in result2

@patch('requests.get')
def test_caching_works(mock_get):
    """Test that results are cached to avoid repeated API calls."""
    mock_json = {"results": [{"term": "Headache", "count": 200}]}
    mock_get.return_value = mock_response(json_data=mock_json)

    # First call - should call the API
    get_top_adverse_events("cacheddrug")
    assert mock_get.call_count == 1

    # Second call - should hit the cache
    get_top_adverse_events("cacheddrug")
    assert mock_get.call_count == 1 # Still 1, not 2

    # Call with different params - should trigger a new API call
    get_top_adverse_events("cacheddrug", limit=20)
    assert mock_get.call_count == 2
