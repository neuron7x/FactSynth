import { useEffect, useState } from 'react';

export default function RateLimitView() {
  const [limit, setLimit] = useState('');

  useEffect(() => {
    fetch('/api/rate-limit')
      .then((r) => r.json())
      .then((data) => setLimit(data.limit))
      .catch(() => setLimit(''));
  }, []);

  const save = () => {
    fetch('/api/rate-limit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: Number(limit) }),
    });
  };

  return (
    <div>
      <h2>Rate Limit</h2>
      <input
        value={limit}
        onChange={(e) => setLimit(e.target.value)}
        type="number"
        min="0"
      />
      <button onClick={save}>Save</button>
    </div>
  );
}
