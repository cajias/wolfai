# Plan to Build a Web Tool for Werewolf AI

1. **Project Setup**
   - Create a new repository or folder structure for web, backend API, and shared assets.
   - Decide on languages/frameworks:
     - Backend: Python with FastAPI or Flask.
     - Frontend: React or Vue with WebSocket support.

2. **Core Backend Service**
   - [x] Skeleton FastAPI app with `/new-game`, `/action`, `/state`, `/end-game` and in-memory session management.
   - Wrap existing Arena logic in an HTTP API:
     - Endpoints: `/new-game`, `/action`, `/state`, `/end-game`.
     - Maintain hidden state server-side to prevent leaks.
   - Implement session/game IDs and state management (in-memory or database).
   - [x] Add WebSockets for live updates.
   - [x] Unit tests for game flow and API stability.

3. **Front-End Application**
   - SPA that connects to API and subscribes to state updates.
   - UI components:
     - Lobby / "start game" screen.
     - Day/night phase views, action prompts (vote, accuse, etc.).
     - Chat or log display for events.
   - Environment configuration to point to backend URL.
   - Cypress or Jest tests for UI flows.

4. **Deployment & Infrastructure**
   - Backend: Containerize with Docker; deploy on Heroku, Render, or similar (include env vars, logging).
   - Frontend: Build static site and deploy to Netlify, Vercel, or GitHub Pages.
   - Configure CORS, SSL, and environment settings.

5. **Game Features & Enhancements**
   - Authentication or matchmaking (optional for MVP).
   - Persistence: database for ongoing games and logs.
   - Monitoring: server logs, analytics to track usage.
   - Scalability: Docker/Kubernetes if multiple sessions expected.

6. **Testing & Quality Assurance**
   - Automated tests for backend logic, front-end interactions, and integrated API flows.
   - Load testing or simulations for concurrent games.
   - Continuous integration pipeline (GitHub Actions or similar).

7. **Roadmap/Milestones**
   - **Milestone 1**: API skeleton with basic game session management.
   - **Milestone 2**: Front-end prototype communicating with API.
   - **Milestone 3**: Deployment of MVP (single human vs. AI).
   - **Milestone 4**: Add real-time updates, polished UI, and logging.
   - **Milestone 5**: Optional features (auth, matchmaking, scaling strategies).

