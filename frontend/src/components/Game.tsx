import React, { useEffect, useState } from 'react';
import { fetchGameState, GameState } from '../api';

export default function Game() {
  const [state, setState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchGameState()
      .then(setState)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!state) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>Game State</h2>
      <pre>{JSON.stringify(state, null, 2)}</pre>
    </div>
  );
}
