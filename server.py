"""
HTTP server for the Release Note Manager UI and JSON API.

Endpoints:
    GET  /                   → serve ui/index.html
    GET  /api/defects        → list all defects (JSON)
    POST /api/defects        → create a defect
    PATCH /api/defects/{id}  → update defect status
    OPTIONS *                → CORS preflight
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import db

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui')


class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):  # noqa: A002
        pass  # suppress default access log

    # ------------------------------------------------------------------
    # CORS helpers
    # ------------------------------------------------------------------
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/':
            self._serve_file(os.path.join(UI_DIR, 'index.html'), 'text/html; charset=utf-8')
        elif path == '/api/defects':
            self._json_response(db.get_all_defects())
        else:
            self._not_found()

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    def do_POST(self):
        path = urlparse(self.path).path

        if path == '/api/defects':
            body = self._read_json()
            if body is None:
                return
            defect_id = db.create_defect(
                title=body.get('title', ''),
                date=body.get('date', ''),
                developer_comment=body.get('developer_comment', ''),
                label=body.get('label', ''),
                status=body.get('status', 'OPEN'),
            )
            self._json_response({'id': defect_id}, status=201)
        else:
            self._not_found()

    # ------------------------------------------------------------------
    # PATCH
    # ------------------------------------------------------------------
    def do_PATCH(self):
        parts = urlparse(self.path).path.strip('/').split('/')
        # Expected: ['api', 'defects', '<id>']
        if len(parts) == 3 and parts[0] == 'api' and parts[1] == 'defects':
            try:
                defect_id = int(parts[2])
            except ValueError:
                self._bad_request("Invalid defect id")
                return

            body = self._read_json()
            if body is None:
                return

            if 'status' in body:
                db.update_defect_status(defect_id, body['status'])

            self._json_response({'id': defect_id, 'status': body.get('status')})
        else:
            self._not_found()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _read_json(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            self._bad_request(str(exc))
            return None

    def _serve_file(self, path, content_type):
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._not_found()

    def _json_response(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self):
        self.send_response(404)
        self._cors_headers()
        self.end_headers()

    def _bad_request(self, msg="Bad request"):
        body = json.dumps({'error': msg}).encode()
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)


def run(host='localhost', port=8080):
    db.init_db()
    server = HTTPServer((host, port), RequestHandler)
    print(f"Release Note Manager running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
