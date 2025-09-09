import { useState } from 'react';
import MetricsView from './views/MetricsView.jsx';
import ApiKeysView from './views/ApiKeysView.jsx';
import RateLimitView from './views/RateLimitView.jsx';

export default function App() {
  const [view, setView] = useState('metrics');

  let content;
  if (view === 'keys') {
    content = <ApiKeysView />;
  } else if (view === 'rate') {
    content = <RateLimitView />;
  } else {
    content = <MetricsView />;
  }

  return (
    <div>
      <nav style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <button onClick={() => setView('metrics')}>Metrics</button>
        <button onClick={() => setView('keys')}>API Keys</button>
        <button onClick={() => setView('rate')}>Rate Limit</button>
      </nav>
      {content}
    </div>
  );
}
