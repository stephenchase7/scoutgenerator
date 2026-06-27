from http.server import BaseHTTPRequestHandler
import json
import os
import httpx
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_PUT(self):
        query = parse_qs(urlparse(self.path).query)
        report_id = query.get('id', [None])[0]

        if not report_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing report ID'}).encode())
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
            return

        supabase_url = os.environ.get('SUPABASE_URL', '').strip()
        supabase_key = os.environ.get('SUPABASE_ANON_KEY', '').strip()

        if not supabase_url or not supabase_key:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Supabase not configured'}).encode())
            return

        try:
            response = httpx.patch(
                f'{supabase_url}/rest/v1/scout_captures?id=eq.{report_id}',
                headers={
                    'Content-Type': 'application/json',
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}',
                    'Prefer': 'return=representation'
                },
                json={
                    'name': data.get('name', ''),
                    'club': data.get('club', ''),
                    'jersey': data.get('jersey', ''),
                    'yob': data.get('yob', ''),
                    'foot': data.get('foot', ''),
                    'phys': data.get('phys', ''),
                    'event': data.get('event', ''),
                    'date': data.get('date') or None,
                    'pos': data.get('pos', ''),
                    'overall': data.get('overall', ''),
                    'press': data.get('press', 0),
                    'grid': json.dumps(data.get('grid', {})),
                    'weapons': json.dumps(data.get('weapons', [])),
                    'notes': data.get('notes', '')
                },
                timeout=30.0
            )

            if response.status_code not in [200, 204]:
                raise ValueError(f"Supabase error: {response.text}")

            result = response.json() if response.text else []

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'report': result}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
