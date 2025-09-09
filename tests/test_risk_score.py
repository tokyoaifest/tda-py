"""
Test risk scoring functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRiskScore:
    """Test risk scoring endpoint."""
    
    def test_risk_score_endpoint_valid_coordinates(self):
        """Test risk score endpoint with valid Tokyo coordinates."""
        # Test with Shibuya coordinates
        lat, lon = 35.6598, 139.7006
        response = client.get(f"/risk/score?lat={lat}&lon={lon}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        expected_fields = ["risk_score", "band", "top_contributors", "lat", "lon"]
        for field in expected_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data["risk_score"], (int, float))
        assert isinstance(data["band"], str)
        assert isinstance(data["top_contributors"], list)
        assert isinstance(data["lat"], (int, float))
        assert isinstance(data["lon"], (int, float))
        
        # Check value ranges
        assert 0 <= data["risk_score"] <= 1
        assert data["band"] in ["low", "medium", "high"]
        assert data["lat"] == lat
        assert data["lon"] == lon
    
    def test_risk_score_invalid_latitude(self):
        """Test risk score endpoint with invalid latitude."""
        response = client.get("/risk/score?lat=91&lon=139.7006")
        assert response.status_code == 400
        
        response = client.get("/risk/score?lat=-91&lon=139.7006")
        assert response.status_code == 400
    
    def test_risk_score_invalid_longitude(self):
        """Test risk score endpoint with invalid longitude."""
        response = client.get("/risk/score?lat=35.6598&lon=181")
        assert response.status_code == 400
        
        response = client.get("/risk/score?lat=35.6598&lon=-181")
        assert response.status_code == 400
    
    def test_risk_score_missing_parameters(self):
        """Test risk score endpoint with missing parameters."""
        # Missing latitude
        response = client.get("/risk/score?lon=139.7006")
        assert response.status_code == 422
        
        # Missing longitude
        response = client.get("/risk/score?lat=35.6598")
        assert response.status_code == 422
        
        # Missing both
        response = client.get("/risk/score")
        assert response.status_code == 422
    
    def test_risk_score_contributors_structure(self):
        """Test that risk contributors have expected structure."""
        lat, lon = 35.6598, 139.7006
        response = client.get(f"/risk/score?lat={lat}&lon={lon}")
        
        assert response.status_code == 200
        data = response.json()
        
        contributors = data["top_contributors"]
        assert isinstance(contributors, list)
        
        if contributors:  # If there are contributors
            for contributor in contributors:
                assert isinstance(contributor, dict)
                expected_fields = ["factor", "value", "description"]
                for field in expected_fields:
                    assert field in contributor
                
                assert isinstance(contributor["factor"], str)
                assert isinstance(contributor["value"], (int, float))
                assert isinstance(contributor["description"], str)
    
    def test_multiple_locations(self):
        """Test risk scores for multiple Tokyo locations."""
        test_locations = [
            (35.6762, 139.6993),  # Shibuya
            (35.6895, 139.6917),  # Shinjuku
            (35.6938, 139.7531),  # Chiyoda
            (35.6584, 139.7519),  # Minato
        ]
        
        for lat, lon in test_locations:
            response = client.get(f"/risk/score?lat={lat}&lon={lon}")
            assert response.status_code == 200
            
            data = response.json()
            assert 0 <= data["risk_score"] <= 1
            assert data["band"] in ["low", "medium", "high"]


class TestShelters:
    """Test shelter finding functionality."""
    
    def test_nearby_shelters_endpoint(self):
        """Test nearby shelters endpoint."""
        lat, lon = 35.6598, 139.7006
        response = client.get(f"/shelters/nearby?lat={lat}&lon={lon}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        expected_fields = ["shelters", "lat", "lon"]
        for field in expected_fields:
            assert field in data
        
        assert isinstance(data["shelters"], list)
        assert len(data["shelters"]) <= 3  # Default limit
        
        # Check shelter structure
        if data["shelters"]:
            shelter = data["shelters"][0]
            expected_shelter_fields = ["id", "name", "lat", "lon", "distance_km", "capacity"]
            for field in expected_shelter_fields:
                assert field in shelter
    
    def test_shelters_with_custom_limit(self):
        """Test shelters endpoint with custom limit."""
        lat, lon = 35.6598, 139.7006
        response = client.get(f"/shelters/nearby?lat={lat}&lon={lon}&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["shelters"]) <= 5
    
    def test_shelters_sorted_by_distance(self):
        """Test that shelters are sorted by distance."""
        lat, lon = 35.6598, 139.7006
        response = client.get(f"/shelters/nearby?lat={lat}&lon={lon}")
        
        assert response.status_code == 200
        data = response.json()
        
        shelters = data["shelters"]
        if len(shelters) > 1:
            # Check that distances are in ascending order
            distances = [shelter["distance_km"] for shelter in shelters]
            assert distances == sorted(distances)