const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface GameState {
  status: string;
}

export async function fetchGameState(): Promise<GameState> {
  const resp = await fetch(`${API_URL}/api/state`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch game state: ${resp.status}`);
  }
  return resp.json();
}
