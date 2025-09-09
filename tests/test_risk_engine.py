"""
Test risk engine functionality.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.services.risk_engine import RiskEngine


class TestRiskEngine:
    """Test the RiskEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RiskEngine()
    
    def test_load_weights_default(self):
        """Test loading default weights when config file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            engine = RiskEngine()
            weights = engine.weights
            
            assert "weights" in weights
            assert isinstance(weights["weights"], dict)
            assert "population_density" in weights["weights"]
    
    def test_load_weights_from_file(self):
        """Test loading weights from config file."""
        mock_weights = {
            "weights": {
                "population_density": 0.3,
                "residential_unit_count": 0.2,
            },
            "bands": {
                "low": [0, 0.4],
                "medium": [0.4, 0.8],
                "high": [0.8, 1.0]
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open'), \
             patch('json.load', return_value=mock_weights):
            
            engine = RiskEngine()
            assert engine.weights == mock_weights
    
    def test_get_risk_band(self):
        """Test risk band calculation."""
        # Test with default bands
        assert self.engine._get_risk_band(0.1) == "low"
        assert self.engine._get_risk_band(0.5) == "medium"
        assert self.engine._get_risk_band(0.8) == "high"
        assert self.engine._get_risk_band(1.0) == "high"
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score_mock_location(self):
        """Test risk score calculation for a mock location."""
        # Mock the data loading
        with patch.object(self.engine, '_load_data'):
            # Set up mock data
            self.engine._grid_data = MagicMock()
            self.engine._grid_data.empty = False
            self.engine._buildings_data = MagicMock()
            self.engine._buildings_data.empty = False
            self.engine._hazard_data = MagicMock()
            self.engine._hazard_data.empty = False
            
            # Mock the helper methods
            with patch.object(self.engine, '_find_containing_cell') as mock_find_cell, \
                 patch.object(self.engine, '_get_nearby_buildings') as mock_nearby:
                
                # Set up mock returns
                mock_find_cell.side_effect = [
                    {"pop_density": 10000},  # grid cell
                    {"liq_rank": 3}          # hazard cell
                ]
                
                mock_buildings = MagicMock()
                mock_buildings.__len__.return_value = 5
                mock_buildings.__getitem__.return_value = mock_buildings
                mock_buildings.get.side_effect = lambda key, default=None: {
                    "use": "residential",
                    "levels": 8
                }.get(key, default)
                mock_buildings.mean.return_value = 8.0
                mock_nearby.return_value = mock_buildings
                
                # Calculate risk score
                result = await self.engine.calculate_risk_score(35.6598, 139.7006)
                
                # Verify result structure
                assert hasattr(result, 'risk_score')
                assert hasattr(result, 'band')
                assert hasattr(result, 'top_contributors')
                assert hasattr(result, 'lat')
                assert hasattr(result, 'lon')
                
                assert 0 <= result.risk_score <= 1
                assert result.band in ["low", "medium", "high"]
                assert isinstance(result.top_contributors, list)
    
    def test_find_containing_cell_empty_data(self):
        """Test finding containing cell with empty data."""
        from shapely.geometry import Point
        import geopandas as gpd
        
        point = Point(139.7006, 35.6598)
        empty_gdf = gpd.GeoDataFrame()
        
        result = self.engine._find_containing_cell(point, empty_gdf)
        assert result is None
    
    def test_get_nearby_buildings_empty_data(self):
        """Test getting nearby buildings with empty data."""
        from shapely.geometry import Point
        import geopandas as gpd
        
        point = Point(139.7006, 35.6598)
        empty_gdf = gpd.GeoDataFrame()
        
        result = self.engine._get_nearby_buildings(point, empty_gdf, 100)
        assert len(result) == 0