#!/usr/bin/env python3
"""
Simple PMTiles range-request server for serving prebuilt vector tiles.
"""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import mimetypes

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


class PMTilesHandler(SimpleHTTPRequestHandler):
    """Custom handler for PMTiles with proper CORS and range request support."""
    
    def end_headers(self):
        """Add CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Range, Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests with range support for PMTiles."""
        if self.path.endswith('.pmtiles'):
            self.serve_pmtiles()
        else:
            super().do_GET()
    
    def serve_pmtiles(self):
        """Serve PMTiles files with proper range request support."""
        # Remove query parameters and leading slash
        file_path = self.path.split('?')[0].lstrip('/')
        full_path = Path(file_path)
        
        if not full_path.exists():
            self.send_error(404, f"File not found: {file_path}")
            return
        
        file_size = full_path.stat().st_size
        
        # Handle range requests
        range_header = self.headers.get('Range')
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            try:
                ranges = range_header.replace('bytes=', '').split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else file_size - 1
                
                # Ensure valid range
                start = max(0, min(start, file_size - 1))
                end = max(start, min(end, file_size - 1))
                content_length = end - start + 1
                
                # Send partial content response
                self.send_response(206)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(content_length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                # Send file data
                with open(full_path, 'rb') as f:
                    f.seek(start)
                    self.wfile.write(f.read(content_length))
                
            except (ValueError, IndexError):
                self.send_error(400, "Invalid range header")
        else:
            # Send full file
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())


def main():
    """Start the PMTiles server."""
    port = int(os.getenv('TILES_PORT', 8080))
    
    # Change to the directory containing PMTiles
    tiles_dir = settings.tiles_dir
    if not tiles_dir.exists():
        print(f"Error: Tiles directory {tiles_dir} does not exist")
        return
    
    os.chdir(tiles_dir.parent)
    
    server = HTTPServer(('localhost', port), PMTilesHandler)
    print(f"Starting PMTiles server on http://localhost:{port}")
    print(f"Serving files from: {tiles_dir.parent}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PMTiles server...")
        server.shutdown()


if __name__ == "__main__":
    main()