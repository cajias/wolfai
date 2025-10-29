# WolfAI Monorepo

Multiplayer Werewolf game with AI players that use advanced reasoning techniques.

## Project Structure

```
wolfai/
├── backend/           # Python FastAPI backend service
│   ├── src/wolfai/   # Backend source code
│   ├── tests/        # Backend tests
│   └── README.md     # Backend documentation
├── frontend/          # React TypeScript frontend
│   ├── src/          # Frontend source code
│   └── package.json  # Frontend dependencies
├── docs/              # Project documentation
└── .github/           # CI/CD workflows
```

## Quick Start

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
pytest  # Run tests
```

### Frontend (React + TypeScript)

```bash
cd frontend
npm install
npm run dev
```

## Development

Each workspace (backend, frontend) has its own README with specific setup and development instructions.

### Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests (when added)
cd frontend && npm test
```

### CI/CD

The project uses GitHub Actions for continuous integration. The workflow:
- Runs on Python 3.11 and 3.12
- Installs dependencies including SWI-Prolog
- Builds the package
- Runs linting (Ruff)
- Executes the test suite

## Documentation

- [README.rst](./README.rst) - Full project documentation
- [GOAL.md](./GOAL.md) - Project goals and vision
- [PLAN.md](./PLAN.md) - Development plan and milestones
- [Backend README](./backend/README.md) - Backend-specific documentation

## Contributing

See [CONTRIBUTING.rst](./CONTRIBUTING.rst) for contribution guidelines.

## License

Not open source - See project metadata for details.
