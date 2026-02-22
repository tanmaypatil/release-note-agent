"""
Section 3 — HTTP server tests.

Requires the server to be running:
    python server.py

Run from the project root:
    python tests/test_server.py [--base-url http://localhost:8080]
"""
import sys
import os
import json
import argparse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = 'http://localhost:8080'


def request(method, path, body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b''


def request_json(method, path, body=None):
    status, raw = request(method, path, body)
    return status, json.loads(raw) if raw else {}


def test_get_defects():
    status, body = request_json('GET', '/api/defects')
    assert status == 200, f'Expected 200, got {status}'
    assert isinstance(body, list), 'Expected a JSON list'
    print(f'GET  /api/defects:          PASS  ({len(body)} defects)')


def test_create_defect():
    status, body = request_json('POST', '/api/defects', {
        'title': 'Server test defect',
        'date': '2024-03-01',
        'label': 'v-test',
        'status': 'OPEN',
        'developer_comment': 'Created by test_server.py',
    })
    assert status == 201, f'Expected 201, got {status}'
    assert 'id' in body, f'Expected id in response, got {body}'
    defect_id = body['id']
    print(f'POST /api/defects:          PASS  (id={defect_id})')
    return defect_id


def test_patch_status(defect_id):
    status, body = request_json('PATCH', f'/api/defects/{defect_id}', {'status': 'RESOLVED'})
    assert status == 200, f'Expected 200, got {status}'
    assert body.get('status') == 'RESOLVED', f'Unexpected body: {body}'
    print(f'PATCH /api/defects/{defect_id}:       PASS  (status=RESOLVED)')


def test_ui_served():
    status, raw = request('GET', '/')
    assert status == 200, f'Expected 200 for UI, got {status}'
    assert b'<html' in raw.lower(), 'Expected HTML response body'
    print('GET  /:                     PASS  (UI served)')


def main():
    global BASE_URL

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default=BASE_URL)
    args = parser.parse_args()

    BASE_URL = args.base_url.rstrip('/')

    print(f'=== HTTP Server  ({BASE_URL}) ===')
    test_get_defects()
    defect_id = test_create_defect()
    test_patch_status(defect_id)
    test_ui_served()
    print('\nAll server tests passed.')


if __name__ == '__main__':
    main()
