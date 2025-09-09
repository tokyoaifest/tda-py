#!/usr/bin/env python3
"""
Build vector tiles from computed risk data using tippecanoe.
This script requires tippecanoe to be installed.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def check_tippecanoe():
    """Check if tippecanoe is available."""
    try:
        result = subprocess.run(['tippecanoe', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def build_risk_tiles():
    """Build risk heatmap tiles from computed data."""
    # Input: computed risk grid
    input_file = Path("data/computed/risk_grid.geojson")
    if not input_file.exists():
        print(f"Error: {input_file} not found. Run 'make compute' first.")
        return False
    
    # Output: PMTiles file
    output_file = settings.tiles_dir / "risk.pmtiles"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Tippecanoe command
    cmd = [
        'tippecanoe',
        '-o', str(output_file),
        '-z', '14',  # Max zoom
        '-Z', '6',   # Min zoom
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '-l', 'risk',  # Layer name
        '--attribution', 'Tokyo Disaster Risk Assessment',
        '--force',  # Overwrite existing file
        str(input_file)
    ]
    
    print(f"Building tiles: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully built tiles: {output_file}")
        print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building tiles: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def build_building_tiles():
    """Build building tiles from mock data."""
    input_file = settings.mock_dir / "buildings.geojson"
    if not input_file.exists():
        print(f"Warning: {input_file} not found, skipping building tiles")
        return True
    
    output_file = settings.tiles_dir / "buildings.pmtiles"
    
    cmd = [
        'tippecanoe',
        '-o', str(output_file),
        '-z', '16',  # Max zoom (higher for building details)
        '-Z', '10',  # Min zoom
        '--drop-densest-as-needed',
        '-l', 'buildings',
        '--force',
        str(input_file)
    ]
    
    print(f"Building building tiles: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully built building tiles: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building building tiles: {e}")
        return False


def main():
    """Main tile building pipeline."""
    print("Starting tile building...")
    
    if not check_tippecanoe():
        print("Error: tippecanoe is not available")
        print("Install tippecanoe: https://github.com/felt/tippecanoe")
        print("On macOS: brew install tippecanoe")
        return
    
    success = True
    
    # Build risk tiles
    if not build_risk_tiles():
        success = False
    
    # Build building tiles
    if not build_building_tiles():
        success = False
    
    if success:
        print("\nTile building completed successfully!")
        print(f"Tiles saved to: {settings.tiles_dir}")
    else:
        print("\nTile building completed with errors")


if __name__ == "__main__":
    main()