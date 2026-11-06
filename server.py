"""Fixed-question demo comparing authored SQL controls with the real sutura CLI."""
import csv
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'commerce-v1' / 'data'
CATALOG = ROOT / 'commerce-v1' / 'catalog'
QUESTIONS = ROOT / 'commerce-v1' / 'questions'
SUTURA_BIN = os.environ.get('SUTURA_BIN', '/usr/local/bin/sutura')
IMAGE = 'ghcr.io/telekom/sutura@sha256:51a04d86c1d87049f01fb80fd6218bbebc21dce6180bbf97693cd741bce4bb2f'
LIMIT = threading.BoundedSemaphore(2)
PERIOD = "o.invoice_date >= '2026-10-01' AND o.invoice_date < '2026-11-01'"
PAID = "o.status = 'paid' AND o.is_production = 1"

SCENARIOS = {
    'october-net': {
        'title': 'A missing refund rule',
        'question': 'What is the net value of October 2026 paid, non-test orders?',
        'description': 'An intentionally incomplete SQL control omits refunds; the approved metric includes them.',
        'baseline_label': 'Authored SQL omitting refund subtraction', 'kind': 'definition',
        'file': 'october-net.yaml',
        'sql': f'SELECT COALESCE(SUM(o.gross_cents), 0) AS value_cents FROM order_facts o WHERE {PERIOD} AND {PAID};',
        'reference': {'description': 'The agreed fixed-snapshot definition gives $375.00 (37,500 cents).', 'rows': [[37500]]},
        'notes': ['This control was deliberately written to omit a rule; it is not an observed AI mistake.',
                  'We aggregated refunds into net_cents before loading sutura. Sutura applies the catalog definition over that prepared data.'],
    },
    'october-regions': {
        'title': 'The same definition in SQL',
        'question': 'What is October 2026 order-cohort net value by region?',
        'description': 'A correct SQL control and the metric runtime should agree. No accuracy advantage is assumed.',
        'baseline_label': 'Authored SQL using the same agreed definition', 'kind': 'agreement',
        'file': 'october-regions.yaml',
        'sql': f'SELECT c.region, SUM(o.net_cents) AS value_cents FROM order_facts o JOIN customers c ON c.customer_id = o.customer_id WHERE {PERIOD} AND {PAID} GROUP BY c.region ORDER BY c.region;',
        'reference': {'description': 'East $145.00 + West $230.00 reconciles to $375.00.', 'rows': [['East', 14500], ['West', 23000]]},
        'notes': ['Both paths read the same prepared per-order data.', 'Agreement here is not evidence that sutura improves model accuracy.'],
    },
    'widget-net': {
        'title': 'Select orders without duplication',
        'question': 'What is October net value for whole orders containing WIDGET?',
        'description': 'The control uses EXISTS; sutura filters a prepared whole-order membership flag.',
        'baseline_label': 'Authored SQL selecting each matching order once', 'kind': 'agreement',
        'file': 'october-widget.yaml',
        'sql': f"SELECT COALESCE(SUM(o.net_cents), 0) AS value_cents FROM order_facts o WHERE {PERIOD} AND {PAID} AND EXISTS (SELECT 1 FROM order_lines l WHERE l.order_id = o.order_id AND l.sku = 'WIDGET');",
        'reference': {'description': 'Whole matching orders contribute $235.00. This is not allocated WIDGET line revenue.', 'rows': [[23500]]},
        'notes': ['contains_widget was prepared by us from order lines before sutura ran.', 'The metric runtime does not automatically repair raw one-to-many joins in this demo.'],
    },
    'scope-change': {
        'title': 'Try to change the approved scope',
        'question': 'Can the approved paid-sales metric be filtered to pending orders?',
        'description': 'An off-contract SQL control can read pending orders; the metric declares no status dimension.',
        'baseline_label': 'Authored off-contract SQL selecting pending orders', 'kind': 'refusal',
        'file': 'refused-undeclared-status.yaml',
        'sql': f"SELECT COALESCE(SUM(o.net_cents), 0) AS value_cents FROM order_facts o WHERE {PERIOD} AND o.status = 'pending' AND o.is_production = 1;",
        'reference': {'description': 'The approved metric should refuse this undeclared dimension rather than change its meaning.', 'rows': []},
        'notes': ['This tests the permitted query surface, not end-user authorization or row-level security.', 'The displayed pending-order control has a different policy from the approved metric.'],
    },
    'unknown-profit': {
        'title': 'Ask for a metric that is absent',
        'question': 'What was October net profit after fulfillment costs and taxes?',
        'description': 'Profit is not defined and the source fixture has no fulfillment cost or tax fields.',
        'baseline_label': 'Unavailable from this fixture', 'kind': 'refusal',
        'file': 'refused-unknown-metric.yaml', 'sql': '',
        'reference': {'description': 'A useful response identifies the missing metric/data instead of returning sales as profit.', 'rows': []},
        'notes': ['No profit calculation is implemented. The real metric request asks for profit and is refused.'],
    },
    'empty-december': {
        'title': 'An empty period is visible',
        'question': 'What is the observed December total in this fixed snapshot?',
        'description': 'The SQL control returns zero via COALESCE; sutura returns no grouped rows.',
        'baseline_label': 'Authored SQL explicitly returning zero for no rows', 'kind': 'empty',
        'file': 'empty-december.yaml',
        'sql': f"SELECT COALESCE(SUM(o.net_cents), 0) AS value_cents FROM order_facts o WHERE o.invoice_date >= '2026-12-01' AND o.invoice_date < '2027-01-01' AND {PAID};",
        'reference': {'description': 'The two empty-result conventions differ. No rows is preserved; it is not silently normalized to zero.', 'rows': []},
        'notes': ['This is an observed empty period in a synthetic snapshot, not a December forecast.', 'Missing source data and genuinely empty periods require separate production checks.'],
    },
    'anchor-drift': {
        'title': 'Change data behind a known answer',
        'question': 'What happens if prepared October net value is accidentally increased by $10?',
        'description': 'A temporary copy changes order 2 by 1,000 cents; both controls read that same changed copy.',
        'baseline_label': 'Authored SQL reading the deliberately changed data', 'kind': 'anchor',
        'file': 'october-net.yaml',
        'sql': f'SELECT COALESCE(SUM(o.net_cents), 0) AS value_cents FROM order_facts o WHERE {PERIOD} AND {PAID};',
        'reference': {'description': 'The fixed October anchor is 37,500 cents. The controlled data error produces 38,500 cents and should fail that check.', 'rows': [[37500]]},
        'notes': ['The extra $10 is a deliberate prepared-data error, not a real customer event.', 'An anchor checks this known result. It is not proof that all data changes or errors are detected.'],
    },
}

LIMITATIONS = [
    'Each Run executes actual sutura query/compile commands. There is no live LLM call.',
    'The SQL controls are authored examples, not outputs from a new AI benchmark.',
    'Refund aggregation and whole-order product membership were prepared by us before sutura execution.',
    'All data is synthetic and fixed. No real business, deployed dashboard or end-user permission model is evaluated.',
    'The demo-v1 label is our packaged definition version; sutura supplies the displayed content digest.',
]


def validate_request(payload):
    if not isinstance(payload, dict) or set(payload) != {'scenario'}:
        raise ValueError('Send exactly one scenario field.')
    name = payload['scenario']
    if not isinstance(name, str) or name not in SCENARIOS:
        raise ValueError('Choose a listed scenario.')
    return name


def parse_query(stdout, stderr, returncode):
    result = {'status': 'answer', 'columns': [], 'rows': [], 'definition_digest': '', 'refusal': None}
    if stdout.startswith('refused: '):
        lines = stdout.strip().splitlines()
        result.update(status='refusal', refusal={'code': lines[0].split(': ', 1)[1], 'detail': '\n'.join(lines[1:]).strip()})
        return result
    if returncode:
        if 'expected to produce' in stderr and 'and produced' in stderr:
            result.update(status='refusal', refusal={'code': 'anchor_check_failed', 'detail': stderr.strip()})
        else:
            result.update(status='error', refusal={'code': 'engine_execution_failed', 'detail': stderr.strip()[:2000] or 'sutura did not complete.'})
        return result
    lines = stdout.splitlines()
    if not lines or not re.fullmatch(r'-- definitions \S+ [a-f0-9]{64}', lines[0]):
        raise ValueError('Unexpected sutura query output.')
    result['definition_digest'] = lines.pop(0).rsplit(' ', 1)[1]
    if not lines:
        raise ValueError('Missing sutura result columns.')
    parsed = list(csv.reader(lines, delimiter='\t'))
    result['columns'] = parsed[0]
    result['rows'] = [row for row in parsed[1:] if row]
    if any(len(row) != len(result['columns']) for row in result['rows']):
        raise ValueError('Malformed sutura result row.')
    return result


def parse_compile(stdout):
    if stdout.startswith('refused: '):
        return '', stdout.strip()
    before_plan = stdout.split('\n-- plan\n', 1)[0]
    sql, params = [], []
    for line in before_plan.splitlines():
        if line.startswith('-- $'):
            params.append(line)
        elif line and not line.startswith('-- '):
            sql.append(line)
    return '\n'.join(sql).strip(), '\n'.join(params)


def prepared_rows(directory):
    with (directory / 'order_facts.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    return rows


def run_baseline(scenario, directory):
    case = SCENARIOS[scenario]
    result = {'label': case['baseline_label'], 'sql': case['sql'], 'columns': [], 'rows': [], 'status': 'answer'}
    if not case['sql']:
        return result | {'status': 'unavailable', 'detail': 'The fixture contains no cost/tax inputs or profit definition.'}
    db = sqlite3.connect(':memory:')
    try:
        db.execute('CREATE TABLE order_facts(order_id INTEGER,customer_id INTEGER,invoice_date TEXT,status TEXT,is_test INTEGER,gross_cents INTEGER,net_cents INTEGER,contains_widget TEXT,is_production INTEGER)')
        for row in prepared_rows(directory):
            db.execute('INSERT INTO order_facts VALUES(?,?,?,?,?,?,?,?,?)',
                       (int(row['order_id']), int(row['customer_id']), row['invoice_date'], row['status'],
                        int(row['is_test'] == 'true'), int(row['gross_cents']), int(row['net_cents']),
                        row['contains_widget'], int(row['is_production'] == 'true')))
        db.execute('CREATE TABLE customers(customer_id INTEGER,region TEXT)')
        with (directory / 'customers.csv').open(newline='') as f:
            db.executemany('INSERT INTO customers VALUES(?,?)', [(int(row['customer_id']), row['region']) for row in csv.DictReader(f)])
        source = json.loads((ROOT / 'source-fixture.json').read_text())
        db.execute('CREATE TABLE order_lines(id INTEGER,order_id INTEGER,sku TEXT,quantity INTEGER,line_gross_cents INTEGER)')
        db.executemany('INSERT INTO order_lines VALUES(?,?,?,?,?)', source['order_lines'])
        cursor = db.execute(case['sql'])
        result['columns'] = [column[0] for column in cursor.description]
        result['rows'] = [list(row) for row in cursor.fetchall()]
        return result
    finally:
        db.close()


def prepare_drift(directory):
    shutil.copytree(DATA, directory, dirs_exist_ok=True)
    rows = prepared_rows(directory)
    fields = list(rows[0])
    for row in rows:
        if row['order_id'] == '2':
            row['net_cents'] = str(int(row['net_cents']) + 1000)
    with (directory / 'order_facts.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return directory


def validate_prepared_data():
    source = json.loads((ROOT / 'source-fixture.json').read_text())
    rows = prepared_rows(DATA)
    if len(rows) != len(source['orders']) or len({row['order_id'] for row in rows}) != len(rows):
        raise ValueError('Prepared order count/key mismatch.')
    for raw, row in zip(source['orders'], rows):
        oid, cid, timestamp, status, is_test, gross = raw
        refunded = sum(r[3] for r in source['refunds'] if r[1] == oid)
        widget = any(line[1] == oid and line[2] == 'WIDGET' for line in source['order_lines'])
        expected = {'order_id': str(oid), 'customer_id': str(cid), 'invoice_date': timestamp[:10],
                    'status': status, 'is_test': str(bool(is_test)).lower(), 'gross_cents': str(gross),
                    'net_cents': str(gross - refunded), 'contains_widget': 'yes' if widget else 'no',
                    'is_production': str(not bool(is_test)).lower()}
        if row != expected:
            raise ValueError('Prepared data differs from the documented transformation.')


def invoke(arguments):
    return subprocess.run([SUTURA_BIN] + arguments, cwd=ROOT / 'commerce-v1',
                          capture_output=True, text=True, timeout=20, check=False)


@lru_cache(maxsize=1)
def catalog_digest():
    result = invoke(['catalog', str(CATALOG)])
    match = re.search(r'^digest\s+([a-f0-9]{64})$', result.stdout, re.M)
    if result.returncode or not match:
        raise ValueError('Could not read the real sutura catalog digest.')
    return match.group(1)


def run_product(scenario, directory):
    started = time.monotonic()
    question = str(QUESTIONS / SCENARIOS[scenario]['file'])
    query = invoke(['query', str(CATALOG), question, str(directory)])
    result = parse_query(query.stdout, query.stderr, query.returncode)
    compiled = invoke(['compile', str(CATALOG), question])
    if compiled.returncode:
        raise ValueError('sutura compile failed: ' + compiled.stderr[:1000])
    sql, parameters = parse_compile(compiled.stdout)
    result.update(sql=sql, parameters=parameters,
                  definition_digest=result['definition_digest'] or catalog_digest(),
                  definition_version='demo-v1', elapsed_ms=round((time.monotonic() - started) * 1000, 1),
                  engine='sutura 0.11.0')
    if result['refusal']:
        result['detail'] = result['refusal']['detail']
    return result


def run_case(scenario):
    validate_request({'scenario': scenario})
    case = SCENARIOS[scenario]
    if scenario == 'anchor-drift':
        with tempfile.TemporaryDirectory(prefix='sutura-demo-drift-') as d:
            directory = prepare_drift(Path(d))
            baseline = run_baseline(scenario, directory)
            product = run_product(scenario, directory)
    else:
        baseline = run_baseline(scenario, DATA)
        product = run_product(scenario, DATA)
    return {'scenario': scenario, 'question': case['question'], 'baseline': baseline,
            'product': product, 'reference': case['reference'], 'notes': case['notes'],
            'live': True, 'llm': False}


def static_path(path):
    route = unquote(urlsplit(path).path)
    route = {'/': '/index.html', '/embed': '/index.html', '/embed/': '/index.html', '/embed.html': '/index.html'}.get(route, route)
    public = ROOT / 'public'
    candidate = (public / route.lstrip('/')).resolve()
    return candidate if public.resolve() in candidate.parents else None


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status, data, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if content_type.startswith('application/json') else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store' if self.path.startswith('/api/') else 'public, max-age=300')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self' https://y9yk.bearblog.dev; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/health':
            self.respond(200, {'status': 'ok', 'engine': 'sutura 0.11.0'})
        elif path == '/api/catalog':
            self.respond(200, {'engine': {'name': 'sutura', 'version': '0.11.0', 'image': IMAGE},
                              'scenarios': [{k: case[k] for k in ('title', 'question', 'description', 'baseline_label', 'kind')} | {'id': name}
                                            for name, case in SCENARIOS.items()], 'limitations': LIMITATIONS,
                              'repository_url': os.environ.get('REPOSITORY_URL', 'https://github.com/y9yk/sutura-sales-demo')})
        elif path == '/api/data':
            self.respond(200, json.loads((ROOT / 'source-fixture.json').read_text()))
        elif path.startswith('/api/'):
            self.respond(404, {'error': 'No such API route.'})
        else:
            target = static_path(self.path)
            if target is None or not target.is_file():
                self.respond(404, {'error': 'Not found.'})
                return
            mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            self.respond(200, target.read_bytes(), mime + ('; charset=utf-8' if mime.startswith('text/') or mime == 'application/javascript' else ''))

    def do_POST(self):
        if urlsplit(self.path).path != '/api/run':
            self.respond(404, {'error': 'No such API route.'})
            return
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            self.respond(415, {'error': 'Use application/json.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if length < 0:
                raise ValueError('A non-negative Content-Length is required.')
            if length > 4096:
                self.respond(413, {'error': 'Request exceeds 4 KB.'})
                return
            scenario = validate_request(json.loads(self.rfile.read(length)))
        except (ValueError, UnicodeError) as error:
            self.respond(400, {'error': str(error)})
            return
        if not LIMIT.acquire(blocking=False):
            self.respond(503, {'error': 'Both demo execution slots are busy. Please try again shortly.'})
            return
        try:
            result = run_case(scenario)
            self.respond(502 if result['product']['status'] == 'error' else 200, result)
        except subprocess.TimeoutExpired:
            self.respond(502, {'error': 'The sutura process exceeded its 20-second budget. No result was substituted.'})
        except (ValueError, OSError, sqlite3.DatabaseError) as error:
            self.respond(502, {'error': 'The real engine comparison could not complete.', 'detail': str(error)[:1200]})
        finally:
            LIMIT.release()


def main():
    validate_prepared_data()
    version = invoke(['--version'])
    if version.returncode or version.stdout.strip() != 'sutura 0.11.0':
        raise RuntimeError('The pinned sutura 0.11.0 binary is required.')
    catalog_digest()
    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f'Demo ready on {host}:{port}; sutura 0.11.0, fixed synthetic data.', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == '__main__':
    main()
