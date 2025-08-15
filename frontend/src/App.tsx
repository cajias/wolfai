import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Lobby from './components/Lobby';
import Game from './components/Game';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/game" element={<Game />} />
      </Routes>
    </BrowserRouter>
  );
}
