"""Run live engine/protocol checks against an already running demo container."""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    def request(path, body=None, content_type='application/json'):
        data = None if body is None else body if isinstance(body, bytes) else json.dumps(body).encode()
        req = urllib.request.Request(args.base_url + path, data=data, headers={'Content-Type': content_type})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    status, catalog = request('/api/catalog')
    assert status == 200 and len(catalog['scenarios']) == 7
    results = {}
    for case in catalog['scenarios']:
        status, data = request('/api/run', {'scenario': case['id']})
        assert status == 200, (case['id'], status, data)
        assert data['live'] is True and data['llm'] is False
        assert data['product']['engine'] == 'sutura 0.11.0'
        assert len(data['product']['definition_digest']) == 64
        results[case['id']] = data
    assert results['october-net']['baseline']['rows'] == [[47000]]
    assert results['october-net']['product']['rows'] == [['2026-10-01', '37500']]
    assert results['october-regions']['product']['rows'] == [['East', '2026-10-01', '14500'], ['West', '2026-10-01', '23000']]
    assert results['widget-net']['product']['rows'] == [['2026-10-01', '23500']]
    assert results['scope-change']['product']['refusal']['code'] == 'DimensionNotPermitted'
    assert results['unknown-profit']['product']['refusal']['code'] == 'MetricUnknown'
    assert results['empty-december']['baseline']['rows'] == [[0]]
    assert results['empty-december']['product']['rows'] == []
    assert results['anchor-drift']['baseline']['rows'] == [[38500]]
    assert results['anchor-drift']['product']['status'] == 'refusal'
    assert '37500' in results['anchor-drift']['product']['refusal']['detail']
    for bad in ({'scenario': 'nope'}, {'scenario': 'october-net', 'sql': 'SELECT 1'}, [], {'scenario': None}):
        assert request('/api/run', bad)[0] == 400
    assert request('/api/run', b'x' * 4097)[0] == 413
    assert request('/api/run', b'{')[0] == 400
    assert request('/api/run', b'{}', 'text/plain')[0] == 415
    assert request('/api/data')[0] == 200
    for path in ('/', '/embed', '/embed.html', '/app.js', '/ui.mjs', '/style.css'):
        with urllib.request.urlopen(args.base_url + path, timeout=10) as response:
            assert response.status == 200
            if path.endswith(('.js', '.mjs')):
                assert 'javascript' in response.headers['Content-Type']
            assert "frame-ancestors 'self' https://y9yk.bearblog.dev" in response.headers['Content-Security-Policy']
    evidence = {'base_url': args.base_url, 'scenarios': results, 'protocol_checks': 'passed'}
    if args.output:
        args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    print('PASS: seven actual sutura scenarios; invalid input, body limits, static MIME and frame policy.')


if __name__ == '__main__':
    main()
