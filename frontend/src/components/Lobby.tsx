import React from 'react';
import { Link } from 'react-router-dom';

export default function Lobby() {
  return (
    <div>
      <h2>Lobby</h2>
      <p>Welcome to WolfAI. When ready, start a new game.</p>
      <Link to="/game">Start Game</Link>
    </div>
  );
}
