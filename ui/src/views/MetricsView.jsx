import { useEffect, useState } from 'react';

export default function MetricsView() {
  const [metrics, setMetrics] = useState('');

  useEffect(() => {
    const fetchMetrics = () => {
      fetch('/prometheus/api/v1/query?query=up')
        .then((r) => r.json())
        .then((data) => setMetrics(JSON.stringify(data.data.result, null, 2)))
        .catch(() => setMetrics('error'));
    };
    fetchMetrics();
    const id = setInterval(fetchMetrics, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <h2>Live Metrics</h2>
      <pre>{metrics}</pre>
    </div>
  );
}
