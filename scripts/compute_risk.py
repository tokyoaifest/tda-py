#!/usr/bin/env python3
"""
Risk computation script for Tokyo Disaster Entrapment Assessment.
Joins mock data layers and computes risk scores for grid cells.
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def load_weights():
    """Load risk calculation weights."""
    weights_path = settings.config_dir / "weights.json"
    if not weights_path.exists():
        print(f"Warning: {weights_path} not found, using default weights")
        return {
            "weights": {
                "population_density": 0.25,
                "residential_unit_count": 0.20,
                "building_stories": 0.15,
                "hazard_liquefaction_rank": 0.25,
                "flood_depth": 0.10,
                "proximity_to_shelter": -0.05
            }
        }
    
    with open(weights_path) as f:
        return json.load(f)


def load_mock_data():
    """Load all mock data files."""
    data = {}
    
    # Load grid
    grid_path = settings.mock_dir / "grid_500m.geojson"
    if grid_path.exists():
        data['grid'] = gpd.read_file(grid_path)
        print(f"Loaded {len(data['grid'])} grid cells")
    else:
        print(f"Warning: {grid_path} not found")
        data['grid'] = gpd.GeoDataFrame()
    
    # Load buildings
    buildings_path = settings.mock_dir / "buildings.geojson"
    if buildings_path.exists():
        data['buildings'] = gpd.read_file(buildings_path)
        print(f"Loaded {len(data['buildings'])} buildings")
    else:
        print(f"Warning: {buildings_path} not found")
        data['buildings'] = gpd.GeoDataFrame()
    
    # Load hazards
    hazard_path = settings.mock_dir / "hazard_liq.geojson"
    if hazard_path.exists():
        data['hazards'] = gpd.read_file(hazard_path)
        print(f"Loaded {len(data['hazards'])} hazard zones")
    else:
        print(f"Warning: {hazard_path} not found")
        data['hazards'] = gpd.GeoDataFrame()
    
    return data


def compute_building_metrics(grid_gdf, buildings_gdf):
    """Compute building-related metrics for each grid cell."""
    if buildings_gdf.empty:
        grid_gdf['residential_unit_count'] = 0
        grid_gdf['avg_building_stories'] = 0
        return grid_gdf
    
    # Ensure same CRS
    if grid_gdf.crs != buildings_gdf.crs:
        buildings_gdf = buildings_gdf.to_crs(grid_gdf.crs)
    
    # Spatial join to get buildings in each grid cell
    joined = gpd.sjoin(buildings_gdf, grid_gdf, how='left', predicate='within')
    
    # Compute metrics per grid cell
    building_metrics = joined.groupby('index_right').agg({
        'units': 'sum',
        'levels': 'mean',
        'use': lambda x: (x == 'residential').sum()
    }).rename(columns={
        'units': 'total_units',
        'levels': 'avg_building_stories',
        'use': 'residential_building_count'
    })
    
    # Merge back to grid
    grid_gdf = grid_gdf.merge(
        building_metrics, 
        left_index=True, 
        right_index=True, 
        how='left'
    ).fillna(0)
    
    return grid_gdf


def compute_hazard_metrics(grid_gdf, hazards_gdf):
    """Compute hazard-related metrics for each grid cell."""
    if hazards_gdf.empty:
        grid_gdf['hazard_liq_rank'] = 1
        return grid_gdf
    
    # Ensure same CRS
    if grid_gdf.crs != hazards_gdf.crs:
        hazards_gdf = hazards_gdf.to_crs(grid_gdf.crs)
    
    # For each grid cell, find overlapping hazard with highest rank
    grid_with_hazards = []
    
    for idx, grid_cell in grid_gdf.iterrows():
        # Find overlapping hazards
        overlapping = hazards_gdf[hazards_gdf.intersects(grid_cell.geometry)]
        
        if not overlapping.empty:
            # Take the highest liquefaction rank
            max_rank = overlapping['liq_rank'].max()
            grid_cell_copy = grid_cell.copy()
            grid_cell_copy['hazard_liq_rank'] = max_rank
            grid_with_hazards.append(grid_cell_copy)
        else:
            # No hazard overlap, use default low risk
            grid_cell_copy = grid_cell.copy()
            grid_cell_copy['hazard_liq_rank'] = 1
            grid_with_hazards.append(grid_cell_copy)
    
    return gpd.GeoDataFrame(grid_with_hazards)


def compute_shelter_proximity(grid_gdf):
    """Compute proximity to nearest shelter (mock)."""
    # Mock shelter locations (Tokyo major evacuation centers)
    shelter_locations = [
        (139.7116, 35.6762),  # Tokyo Metropolitan Gymnasium
        (139.7006, 35.6598),  # Shibuya
        (139.6917, 35.6935),  # Shinjuku
        (139.7519, 35.6584),  # Minato
        (139.7531, 35.6938),  # Chiyoda
    ]
    
    shelter_distances = []
    
    for idx, grid_cell in grid_gdf.iterrows():
        # Get centroid of grid cell
        centroid = grid_cell.geometry.centroid
        
        # Calculate distance to nearest shelter (rough approximation)
        min_distance = float('inf')
        for shelter_lon, shelter_lat in shelter_locations:
            # Simple Euclidean distance (approximate)
            distance = np.sqrt(
                (centroid.x - shelter_lon)**2 + 
                (centroid.y - shelter_lat)**2
            ) * 111000  # Rough conversion to meters
            min_distance = min(min_distance, distance)
        
        shelter_distances.append(min_distance)
    
    grid_gdf['shelter_distance_m'] = shelter_distances
    return grid_gdf


def compute_risk_scores(grid_gdf, weights_config):
    """Compute final risk scores for each grid cell."""
    weights = weights_config['weights']
    
    # Normalize factors to 0-1 range
    normalized_factors = {}
    
    # Population density (normalize by max value)
    if 'pop_density' in grid_gdf.columns:
        max_pop = grid_gdf['pop_density'].max() if grid_gdf['pop_density'].max() > 0 else 1
        normalized_factors['population_density'] = grid_gdf['pop_density'] / max_pop
    else:
        normalized_factors['population_density'] = np.zeros(len(grid_gdf))
    
    # Residential units (normalize by reasonable max)
    if 'total_units' in grid_gdf.columns:
        normalized_factors['residential_unit_count'] = np.clip(grid_gdf['total_units'] / 100.0, 0, 1)
    else:
        normalized_factors['residential_unit_count'] = np.zeros(len(grid_gdf))
    
    # Building stories (normalize by reasonable max)
    if 'avg_building_stories' in grid_gdf.columns:
        normalized_factors['building_stories'] = np.clip(grid_gdf['avg_building_stories'] / 30.0, 0, 1)
    else:
        normalized_factors['building_stories'] = np.zeros(len(grid_gdf))
    
    # Hazard liquefaction rank (already 1-5, normalize to 0-1)
    if 'hazard_liq_rank' in grid_gdf.columns:
        normalized_factors['hazard_liquefaction_rank'] = (grid_gdf['hazard_liq_rank'] - 1) / 4.0
    else:
        normalized_factors['hazard_liquefaction_rank'] = np.zeros(len(grid_gdf))
    
    # Flood depth (mock - set to 0 for now)
    normalized_factors['flood_depth'] = np.zeros(len(grid_gdf))
    
    # Proximity to shelter (inverse - closer is better, normalize by max distance)
    if 'shelter_distance_m' in grid_gdf.columns:
        max_distance = grid_gdf['shelter_distance_m'].max() if grid_gdf['shelter_distance_m'].max() > 0 else 1
        normalized_factors['proximity_to_shelter'] = grid_gdf['shelter_distance_m'] / max_distance
    else:
        normalized_factors['proximity_to_shelter'] = np.ones(len(grid_gdf)) * 0.5
    
    # Calculate weighted risk score
    risk_scores = np.zeros(len(grid_gdf))
    
    for factor, values in normalized_factors.items():
        if factor in weights:
            risk_scores += weights[factor] * values
            # Add normalized factors to dataframe for inspection
            grid_gdf[f'norm_{factor}'] = values
    
    # Normalize final scores to 0-1
    risk_scores = np.clip(risk_scores, 0, 1)
    grid_gdf['risk_score'] = risk_scores
    
    # Assign risk bands
    def get_risk_band(score):
        if score < 0.33:
            return 'low'
        elif score < 0.67:
            return 'medium'
        else:
            return 'high'
    
    grid_gdf['risk_band'] = grid_gdf['risk_score'].apply(get_risk_band)
    
    return grid_gdf


def save_results(grid_gdf, output_path):
    """Save computed risk grid to GeoJSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid_gdf.to_file(output_path, driver='GeoJSON')
    print(f"Saved risk grid with {len(grid_gdf)} cells to {output_path}")
    
    # Print summary statistics
    print("\nRisk Score Summary:")
    print(f"Mean risk score: {grid_gdf['risk_score'].mean():.3f}")
    print(f"Risk band distribution:")
    print(grid_gdf['risk_band'].value_counts())


def main():
    """Main computation pipeline."""
    print("Starting risk computation...")
    
    # Load configuration and data
    weights_config = load_weights()
    data = load_mock_data()
    
    if data['grid'].empty:
        print("Error: No grid data found")
        return
    
    grid_gdf = data['grid'].copy()
    
    # Ensure consistent CRS
    if grid_gdf.crs is None:
        grid_gdf = grid_gdf.set_crs("EPSG:4326")
        print("Set grid CRS to EPSG:4326")
    
    # Compute building metrics
    print("Computing building metrics...")
    grid_gdf = compute_building_metrics(grid_gdf, data['buildings'])
    
    # Compute hazard metrics
    print("Computing hazard metrics...")
    grid_gdf = compute_hazard_metrics(grid_gdf, data['hazards'])
    
    # Compute shelter proximity
    print("Computing shelter proximity...")
    grid_gdf = compute_shelter_proximity(grid_gdf)
    
    # Compute final risk scores
    print("Computing risk scores...")
    grid_gdf = compute_risk_scores(grid_gdf, weights_config)
    
    # Save results
    output_path = Path("data/computed/risk_grid.geojson")
    save_results(grid_gdf, output_path)
    
    print("Risk computation completed successfully!")


if __name__ == "__main__":
    main()