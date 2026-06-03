```
██     ██  ██████  ██      ███████  █████  ██
██     ██ ██    ██ ██      ██      ██   ██ ██
██  █  ██ ██    ██ ██      █████   ███████ ██
██ ███ ██ ██    ██ ██      ██      ██   ██ ██
 ███ ███   ██████  ███████ ██      ██   ██ ██
```

<p align="center">
  <strong>A multiplayer Werewolf engine with a FastAPI core, real-time WebSockets, and Prolog-backed AI reasoning.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/cajias/wolfai" alt="Last commit">
  <img src="https://img.shields.io/github/languages/top/cajias/wolfai" alt="Top language">
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue" alt="Python 3.11 | 3.12">
  <img src="https://img.shields.io/badge/api-FastAPI-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb" alt="React + Vite">
  <img src="https://img.shields.io/badge/reasoning-Prolog-cc3333" alt="Prolog">
</p>

---

WolfAI is a monorepo for **Werewolf** — the social-deduction game where hidden
werewolves try to outlast the village. The backend is a complete, server-authoritative
game engine wrapped in a FastAPI REST + WebSocket API, so hidden roles never leak to the
client. Alongside the engine sits a Prolog reasoning layer: an agent that turns natural
language into logical Prolog statements and executes them over the
[Model Context Protocol](https://modelcontextprotocol.io), giving AI players a foundation
for contradiction-checking and deductive inference. A small React + Vite frontend connects
to the API to drive games from the browser.

## ✨ Features

- **Complete Werewolf engine** (`backend/src/wolfai/arena.py`) — roles (Villager, Werewolf,
  Seer, Doctor), six explicit game phases (initialized → night → day → voting → resolution →
  game over), voting and win-condition detection, all driven by a deterministic state machine.
- **Server-authoritative state** — public game state and per-player private views are modeled
  separately (`public_view()` vs `get_player_view()`), so a player only ever sees what their
  role is allowed to know.
- **FastAPI REST + WebSocket API** (`backend/src/wolfai/api.py`) — eight endpoints to create
  games, submit actions, list and poll state, fetch per-player and valid-action views, and
  subscribe to live updates over a WebSocket.
- **Prolog reasoning agent** (`backend/src/wolfai/agents/prolog.py`) — a LangGraph/LangChain
  agent that converts natural language into Prolog and runs it through a Prolog engine
  (`pyswip` + SWI-Prolog) for logical deduction.
- **MCP tool infrastructure** (`backend/src/wolfai/tools/`) — a server factory that turns any
  Python module into a Model Context Protocol server from type hints, plus a standalone Prolog
  MCP server (`tools/pl/`) speaking stdio or SSE.
- **React + Vite frontend** (`frontend/`) — a lightweight TypeScript SPA with a lobby and
  in-game view that talks to the backend API.

## 🚀 Installation

The repo is an npm-workspace monorepo; the two workspaces are installed independently.

### Backend (Python 3.11 / 3.12)

SWI-Prolog is required for the Prolog reasoning layer.

```bash
# install SWI-Prolog (macOS)
brew install swi-prolog

cd backend
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install -e ".[dev]"            # editable install with dev extras
```

> The Prolog reasoning agent calls an LLM and expects an `OPENAI_API_KEY` in the environment.
> The game engine and API run without it.

### Frontend (Node)

```bash
cd frontend
npm install
```

## 🕹️ Usage

### Run the API

The backend is an ASGI app (`wolfai.api:app`). Serve it with uvicorn:

```bash
cd backend
uvicorn wolfai.api:app --reload
```

Endpoints (see [`backend/README.md`](./backend/README.md) for details):

| Method | Path                                  | Purpose                          |
| ------ | ------------------------------------- | -------------------------------- |
| `POST` | `/new-game`                           | Create a new game session        |
| `GET`  | `/games`                              | List active sessions             |
| `GET`  | `/state/{game_id}`                    | Get current public game state    |
| `GET`  | `/player-view/{game_id}/{player_id}`  | Get a player's private view      |
| `GET`  | `/valid-actions/{game_id}/{player_id}`| List a player's valid actions    |
| `POST` | `/action`                             | Submit a player action           |
| `POST` | `/end-game`                           | End a game session               |
| `WS`   | `/ws/{game_id}`                       | Real-time game-state updates     |

### Run the frontend

```bash
cd frontend
npm run dev      # start the Vite dev server
npm run build    # production build
```

### Run the Prolog MCP server

The Prolog tools can be served standalone as an MCP server:

```bash
cd backend
python -m wolfai.tools.pl.prolog_mcp_server --transport stdio
python -m wolfai.tools.pl.prolog_mcp_server --transport sse --port 8000
```

## 🗂️ Project Structure

```
wolfai/
├── backend/                         # Python FastAPI backend (workspace)
│   ├── src/wolfai/
│   │   ├── api.py                   # FastAPI REST + WebSocket endpoints
│   │   ├── arena.py                 # Werewolf engine (roles, phases, voting)
│   │   ├── agents/
│   │   │   └── prolog.py            # LangGraph agent: natural language → Prolog
│   │   ├── tools/                   # Tool integrations
│   │   │   ├── langchain_utils.py   # MCP tools → LangChain tools
│   │   │   ├── mcp_server_factory.py# Module → MCP server factory
│   │   │   └── pl/                  # Prolog engine + MCP Prolog server
│   │   └── logging/                 # Logging configuration
│   ├── tests/                       # pytest suite (unit, e2e/BDD, tools, agents)
│   ├── pyproject.toml               # Python project + tooling config
│   └── README.md                    # Backend-specific docs
├── frontend/                        # React + TypeScript SPA (workspace)
│   ├── src/                         # App, Lobby, Game components + API client
│   ├── vite.config.ts               # Vite config
│   └── package.json
├── docs/                            # Sphinx documentation
├── scripts/                         # Helper scripts (Python lint fixers)
├── package.json                     # Monorepo workspaces + lint/test scripts
├── GOAL.md / PLAN.md                # Project goals and roadmap
└── README.rst                       # Long-form design notes
```

## 🛠️ Development

Top-level npm scripts wrap the backend's Ruff/pylint/pytest tooling:

```bash
npm run lint:py      # Ruff + duplicate-code (pylint) checks
npm run lint:py:fix  # auto-fix Python lint issues
npm run test:py      # run the backend pytest suite
npm run test:e2e     # run the end-to-end BDD tests
```

Or run the backend tooling directly:

```bash
cd backend
ruff check .         # lint
pytest               # tests
python -m build      # build the package
```

CI (GitHub Actions, `.github/workflows/ci.yml`) runs on Python 3.11 and 3.12: it installs
SWI-Prolog, builds the package, lints with Ruff, and runs the test suite.

## 🤝 Contributing

Contributions are welcome. Please open an issue to discuss substantial changes first, keep
PRs focused, and ensure `npm run lint:py` and `npm run test:py` pass. See
[CONTRIBUTING.rst](./CONTRIBUTING.rst) for full guidelines and
[CODE_OF_CONDUCT.rst](./CODE_OF_CONDUCT.rst) for community standards.

## 📄 License

This project is **not open source**. All rights reserved by the author
(see the `license` field in [`backend/pyproject.toml`](./backend/pyproject.toml)). Please
contact the maintainer before any reuse or redistribution.
