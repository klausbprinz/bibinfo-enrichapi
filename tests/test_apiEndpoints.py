from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

# import FastAPI app
from enrichapi.main import app

# import response models
from enrichapi.models.request import OeNBRequestData
from enrichapi.models.response import OenbResponse


@pytest.fixture
def client() -> TestClient:
    """Provides an in-memory TestClient connected to your FastAPI app."""
    return TestClient(app)


# 1. test: successful POST /enrich request (mocking baseFetchOeNB)
def testEnrichEndpointOenbSuccess(client: TestClient):
    """Verify POST /enrich with a valid OeNB payload routes correctly and wraps response."""
    
    payload = {
        "iType": "bib",
        "institution": {
            "iName": "oenb",
            "identifier": "AC12345678",
            "identifierType": "ac",
            "fetchMarc21MD": False,  # set False for lightweight mock testing
            "fetchLobidGND": False,
            "fetchWikidata": False,
            "fetchCover": False,
            "fetchDescription": False
        }
    }
    
    # Construct a valid dummy OenbResponse instance
    mockResult = OenbResponse(
        identifier="AC12345678",
        identifierType="ac",
        basicMarc21MD=None,
        additionalRecsSRU=None,
        gndInfoLobid=None,
        wikidataData=None,
        bookCover=None,
        bookDescription=None
    )

    # Patch the AsyncMock handler inside ENRICHMENT_STRATEGIES
    mockHandler = AsyncMock(return_value=mockResult)

    with patch.dict("enrichapi.main.ENRICHMENT_STRATEGIES", {OeNBRequestData: mockHandler}):
        
        response = client.post("/enrich", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify envelope structure: RootApiResponse -> BibliographicLibraryResponse -> OenbResponse
        assert "response" in data
        assert "result" in data["response"]
        
        result = data["response"]["result"]
        assert result["identifier"] == "AC12345678"
        assert result["identifierType"] == "ac"
        
        mockHandler.assert_called_once()


# 2. test: invalid / missing discriminators (422 Unprocessable Entity)
def testEnrichEndpointInvalidInstitutionType(client: TestClient):
    """Verify 422 error when iName discriminator is invalid or missing."""
    payload = {
        "iType": "bib",
        "institution": {
            "iName": "unknown_library",  # invalid iName (not "oenb")
            "identifier": "AC12345678"
        }
    }
    
    response = client.post("/enrich", json=payload)
    assert response.status_code == 422  # Pydantic discriminator validation failed


# 3. test: unsupported iType (400 Bad Request)
def testEnrichEndpointUnsupportedItype(client: TestClient):
    """Verify 422 or 400 error when iType is unsupported."""
    payload = {
        "iType": "invalid_type",
        "institution": {
            "iName": "oenb",
            "identifier": "AC12345678"
        }
    }
    
    response = client.post("/enrich", json=payload)
    assert response.status_code == 422


# 4. test: maxRecs Range Validation
def testEnrichEndpointMaxRecsValidation(client: TestClient):
    """Verify pydantic ge=1, le=50 rule on maxRecs field."""
    payload = {
        "iType": "bib",
        "institution": {
            "iName": "oenb",
            "identifier": "AC12345678",
            "maxRecs": 100  # Exceeds le=50 constraint
        }
    }
    
    response = client.post("/enrich", json=payload)
    assert response.status_code == 422