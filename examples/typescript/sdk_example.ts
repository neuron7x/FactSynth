// TypeScript SDK example (minimal fetch)
export async function generate(prompt: string, maxTokens = 128, apiBase = '') {
  const r = await fetch(`${apiBase}/v1/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, max_tokens: maxTokens }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// Usage:
// import { generate } from './sdk_example';
// generate('hello', 128, 'http://localhost:8000').then(console.log);
