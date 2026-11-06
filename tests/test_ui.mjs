import test from 'node:test';
import assert from 'node:assert/strict';
import { dollars, outcome } from '../public/ui.mjs';
import * as ui from '../public/ui.mjs';

test('display exact integer cents in dollars without treating missing values as zero', () => {
  assert.equal(dollars('37500'), '$375.00');
  assert.equal(dollars(0), '$0.00');
  assert.equal(dollars(-2500), '-$25.00');
  assert.equal(dollars(''), null);
  assert.equal(dollars(null), null);
});
test('empty rows remain distinct from an observed scalar zero', () => {
  assert.equal(outcome({ status: 'answer', rows: [] }).state, 'No rows');
  assert.equal(outcome({ status: 'answer', rows: [[0]] }).amount, '$0.00');
});
test('refusal text takes precedence over any rows rather than claiming success', () => {
  const result = outcome({ status: 'refusal', rows: [[37500]], refusal: { code: 'metric_unknown', detail: 'Profit is absent.' } });
  assert.equal(result.state, 'Refused');
  assert.equal(result.detail, 'Profit is absent.');
  assert.equal(result.amount, undefined);
});
test('regional answers stay a table; unavailable input is not an execution success', () => {
  assert.equal(outcome({ status: 'answer', rows: [['East', 14500], ['West', 23000]] }).table, true);
  assert.equal(outcome({ status: 'unavailable', rows: [] }).state, 'Unavailable');
  assert.equal(outcome({ status: 'answer' }).state, 'Error');
});
test('surface real nested engine errors and reject empty error messages', () => {
  assert.equal(typeof ui.responseError, 'function');
  assert.equal(ui.responseError({ product: { detail: 'Actual engine failure.' } }), 'Actual engine failure.');
  assert.equal(ui.responseError({ product: { refusal: { detail: 'Catalog could not execute.' } } }), 'Catalog could not execute.');
  assert.equal(ui.responseError({ error: '' }), 'The server could not complete this run.');
});
