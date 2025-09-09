import { useEffect, useState } from 'react';

export default function ApiKeysView() {
  const [keys, setKeys] = useState([]);
  const [description, setDescription] = useState('');

  const load = () => {
    fetch('/api/keys')
      .then((r) => r.json())
      .then(setKeys)
      .catch(() => setKeys([]));
  };

  useEffect(() => {
    load();
  }, []);

  const createKey = () => {
    fetch('/api/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    }).then(load);
  };

  const deleteKey = (id) => {
    fetch(`/api/keys/${id}`, { method: 'DELETE' }).then(load);
  };

  return (
    <div>
      <h2>API Keys</h2>
      <div>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="description"
        />
        <button onClick={createKey}>Create</button>
      </div>
      <ul>
        {keys.map((k) => (
          <li key={k.id}>
            {k.id} - {k.description}{' '}
            <button onClick={() => deleteKey(k.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
