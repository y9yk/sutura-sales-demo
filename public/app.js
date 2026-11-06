import { dollars, outcome, responseError } from './ui.mjs';

const $ = (id) => document.getElementById(id);
const descriptions = {
  'october-net': 'A deliberately incomplete refund rule',
  'october-regions': 'A correct SQL control, same definition',
  'widget-net': 'Whole orders containing the product',
  'scope-change': 'A request outside the declared scope',
  'unknown-profit': 'A metric the catalog does not define',
  'empty-december': 'Empty rows remain different from zero',
  'anchor-drift': 'A controlled data-error check',
};
const headers = {
  customers: ['Customer ID', 'Region'],
  orders: ['Order ID', 'Customer ID', 'Invoice timestamp', 'Status', 'Test flag', 'Gross cents'],
  order_lines: ['Line ID', 'Order ID', 'SKU', 'Quantity', 'Line gross cents'],
  refunds: ['Refund ID', 'Order ID', 'Processed timestamp', 'Amount cents'],
};
let catalog;
let selected;
let pending = false;
let sourceData;
let hasOutput = false;

if (location.pathname.startsWith('/embed')) document.body.classList.add('embed');

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function setStatus(text, error = false) {
  $('run-status').textContent = text;
  $('run-status').classList.toggle('error', error);
}

function table(columns, rows, monetary = false) {
  const node = document.createElement('table');
  const head = node.createTHead().insertRow();
  columns.forEach((name) => { const th = element('th', String(name).replaceAll('_', ' ')); th.scope = 'col'; head.append(th); });
  const body = node.createTBody();
  rows.forEach((values) => {
    const row = body.insertRow();
    values.forEach((value, index) => {
      const cell = row.insertCell();
      cell.textContent = monetary && index === values.length - 1 ? dollars(value) ?? String(value) : String(value ?? 'null');
    });
  });
  return node;
}

function renderOutput(prefix, result) {
  const box = $(prefix + '-output');
  const display = outcome(result);
  $(prefix + '-state').textContent = display.state;
  box.replaceChildren();
  if (display.amount) box.append(element('p', display.amount, 'amount'));
  else if (display.table) box.append(table(result.columns || [], result.rows, true));
  else box.append(element('p', display.heading, 'status-heading'));
  if (result.refusal?.code) box.append(element('span', result.refusal.code, 'result-code'));
  box.append(element('p', display.detail, 'result-detail'));
}

function choose(id) {
  if (pending) return;
  selected = catalog.scenarios.find((scenario) => scenario.id === id);
  if (!selected) return;
  document.querySelectorAll('.scenario-button').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.id === id)));
  $('question-heading').textContent = selected.question;
  $('question-description').textContent = selected.description;
  $('baseline-label').textContent = selected.baseline_label;
  $('finding').hidden = true;
  hasOutput = false;
  ['baseline', 'product'].forEach((prefix) => {
    $(prefix + '-state').textContent = 'Not run';
    $(prefix + '-output').replaceChildren(element('p', 'Run this scenario to see the actual result.', 'placeholder'));
  });
  $('baseline-sql').textContent = 'No execution for this scenario yet.';
  $('product-sql').textContent = 'No execution for this scenario yet.';
  $('product-evidence').textContent = 'No execution for this scenario yet.';
  setStatus('Ready. Each run calls the actual pinned sutura binary.');
  $('run').disabled = false;
}

async function run() {
  if (!selected || pending) return;
  pending = true;
  $('run').disabled = true;
  $('run').firstChild.textContent = 'Running… ';
  document.querySelector('.experiment').setAttribute('aria-busy', 'true');
  document.querySelectorAll('.scenario-button').forEach((button) => { button.disabled = true; });
  setStatus('Executing comparison SQL and the actual sutura query…');
  try {
    const response = await fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ scenario: selected.id }), signal: AbortSignal.timeout(60000) });
    const data = await response.json();
    if (!response.ok) throw new Error(responseError(data));
    if (!data.live || data.llm !== false || !data.product) throw new Error('The server did not return a live product execution.');
    renderOutput('baseline', data.baseline);
    renderOutput('product', data.product);
    $('baseline-label').textContent = data.baseline.label;
    $('baseline-sql').textContent = data.baseline.sql || data.baseline.detail || 'No SQL calculation is defined for this request.';
    $('product-sql').textContent = [data.product.sql || 'No SQL was executed for this refused request.', data.product.parameters || ''].filter(Boolean).join('\n\n');
    $('product-evidence').textContent = JSON.stringify({ engine: data.product.engine, definition_version: data.product.definition_version, definition_digest: data.product.definition_digest || null, columns: data.product.columns, rows: data.product.rows, refusal: data.product.refusal || null }, null, 2);
    $('finding-body').replaceChildren();
    if (data.reference?.description) $('finding-body').append(element('p', data.reference.description));
    (data.notes || []).forEach((note) => $('finding-body').append(element('p', note)));
    $('finding').hidden = false;
    hasOutput = true;
    const time = Number.isFinite(data.product.elapsed_ms) ? `${Math.round(data.product.elapsed_ms)} ms for this product request` : 'Product execution recorded';
    setStatus(`Executed ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} · ${time} · no LLM call`);
  } catch (error) {
    if (hasOutput) ['baseline', 'product'].forEach((prefix) => { $(prefix + '-state').textContent = 'Previous run'; });
    setStatus(`Run failed: ${error.message}. ${hasOutput ? 'Displayed results belong to the previous run. ' : ''}No fallback result has been substituted.`, true);
  } finally {
    pending = false;
    $('run').disabled = false;
    $('run').firstChild.textContent = 'Run comparison ';
    document.querySelector('.experiment').removeAttribute('aria-busy');
    document.querySelectorAll('.scenario-button').forEach((button) => { button.disabled = false; });
  }
}

function renderSource(name) {
  const values = sourceData[name];
  if (!Array.isArray(values)) return;
  $('data-output').replaceChildren(table(headers[name] || [], values));
  document.querySelectorAll('.data-tabs button').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.table === name)));
}

async function loadSource() {
  if (sourceData) return;
  try {
    const response = await fetch('/api/data');
    if (!response.ok) throw new Error('Source data is unavailable.');
    sourceData = await response.json();
    Object.keys(headers).forEach((name) => {
      const button = element('button', name.replaceAll('_', ' '));
      button.type = 'button'; button.dataset.table = name;
      button.addEventListener('click', () => renderSource(name));
      $('data-tabs').append(button);
    });
    renderSource('orders');
  } catch (error) {
    $('data-output').replaceChildren(element('p', error.message, 'muted'));
  }
}

async function init() {
  $('run').addEventListener('click', run);
  $('data-details').addEventListener('toggle', () => { if ($('data-details').open) loadSource(); });
  try {
    const response = await fetch('/api/catalog');
    if (!response.ok) throw new Error('The demo service is not ready.');
    catalog = await response.json();
    if (!Array.isArray(catalog.scenarios) || catalog.scenarios.length === 0) throw new Error('No scenarios were returned.');
    $('engine-label').textContent = `sutura ${catalog.engine.version} · pinned release`;
    $('scenario-list').replaceChildren();
    catalog.scenarios.forEach((scenario) => {
      const button = element('button', undefined, 'scenario-button');
      button.type = 'button'; button.dataset.id = scenario.id;
      button.setAttribute('aria-pressed', 'false');
      button.append(element('span', scenario.title, 'scenario-title'), element('span', descriptions[scenario.id] || scenario.description, 'scenario-subtitle'));
      button.addEventListener('click', () => choose(scenario.id));
      $('scenario-list').append(button);
    });
    if (catalog.repository_url && /^https:\/\/github\.com\//.test(catalog.repository_url)) {
      for (const id of ['repository', 'source-bottom']) { $(id).href = catalog.repository_url; $(id).textContent = 'Source & setup ↗'; $(id).target = '_blank'; $(id).rel = 'noopener'; }
    }
    const requested = new URLSearchParams(location.search).get('scenario');
    choose(catalog.scenarios.some((scenario) => scenario.id === requested) ? requested : catalog.scenarios[0].id);
  } catch (error) {
    $('engine-label').textContent = 'Demo unavailable';
    $('scenario-list').replaceChildren(element('p', 'The live scenario catalog could not be loaded.', 'muted'));
    setStatus(error.message, true);
  }
}

init();
