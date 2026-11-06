export function dollars(cents) {
  if ((typeof cents !== 'number' && typeof cents !== 'string') || String(cents).trim() === '' || !Number.isFinite(Number(cents))) return null;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(Number(cents) / 100);
}

export function responseError(data) {
  const messages = [data.error, data.detail, data.product?.detail, data.product?.refusal?.detail];
  return messages.find((value) => typeof value === 'string' && value.trim()) || 'The server could not complete this run.';
}

export function outcome(result) {
  if (result.status === 'refusal') return { state: 'Refused', heading: 'Request refused', detail: result.refusal?.detail || result.detail || 'The declared metric does not permit this request.' };
  if (result.status === 'error') return { state: 'Error', heading: 'Execution failed', detail: result.detail || result.refusal?.detail || 'The engine did not return an answer.' };
  if (result.status === 'unavailable') return { state: 'Unavailable', heading: 'Not defined', detail: result.detail || 'Required information is absent from this fixture.' };
  if (!Array.isArray(result.rows)) return { state: 'Error', heading: 'Invalid response', detail: 'No result rows were supplied.' };
  if (result.rows.length === 0) return { state: 'No rows', heading: 'No rows', detail: 'The engine returned an empty result. This has not been converted to a scalar zero.' };
  if (result.rows.length === 1) {
    const amount = dollars(result.rows[0].at(-1));
    if (amount !== null) return { state: 'Returned', amount, detail: 'USD · result from this request' };
  }
  return { state: 'Returned', table: true, detail: 'Returned rows · monetary values displayed in USD' };
}
