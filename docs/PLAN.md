# Project Plan (MVP)

This document is the execution checklist for the full MVP.
The sequence is intentional. Do not start the next part until the current part passes its success criteria.

## Confirmed Decisions

- Frontend stack: Next.js (existing app in `frontend/`)
- Backend stack: FastAPI in `backend/`
- Packaging: single Docker container running backend and serving frontend static build at `/`
- Python package manager: `uv`
- Auth approach: backend-enforced session auth (dummy credentials: `user` / `password`)
- Database: SQLite local file, auto-created if missing
- Data model direction: Kanban data saved per `user_id` and `board_id` (JSON payload)
- AI provider/model: OpenRouter with `openai/gpt-oss-120b:free`
- AI safety boundary: backend is source of truth and validates all structured output updates before persist
- Test defaults: backend `pytest`; frontend unit `vitest` + React Testing Library; e2e `playwright`

## Part 1 - Plan and Documentation

### Checklist

- [x] Expand this plan into detailed checklists with tests and success criteria for Parts 2-10
- [x] Document all confirmed architecture decisions and constraints in this file
- [x] Create `frontend/AGENTS.md` describing current frontend code, behavior, and test setup
- [x] Review plan with user and get explicit approval before implementation

### Tests

- [x] Manual review that every part has: scope, actionable checklist, tests, and success criteria
- [x] Manual review that `frontend/AGENTS.md` accurately matches existing frontend files and behavior

### Success Criteria

- [x] User confirms Part 1 documents are acceptable
- [x] No code implementation beyond documentation is performed in Part 1

## Part 2 - Scaffolding

### Checklist

- [x] Create `backend/` FastAPI app with health and hello-world API route
- [x] Add backend dependency management using `uv`
- [x] Create Dockerfile for single-container flow
- [x] Add scripts in `scripts/` to start and stop on Windows, macOS, Linux
- [x] Configure backend to serve a temporary static HTML page at `/` for early validation
- [x] Ensure temporary page can call a backend API endpoint successfully
- [x] Add backend test scaffolding for API smoke checks

### Tests

- [x] `pytest` passes for backend smoke tests
- [x] Docker build succeeds
- [x] Container runs locally and serves temporary page at `/`
- [x] Temporary frontend page can call hello-world API route

### Success Criteria

- [x] Local Docker run proves backend + static serving + API roundtrip works
- [ ] Start/stop scripts work on target OSes
- [ ] Windows script flow verified; macOS/Linux runtime verification still pending on those platforms

## Part 3 - Add Frontend

### Checklist

- [x] Integrate existing Next.js app build into container workflow
- [x] Build frontend statically as part of container build/release process
- [x] Replace temporary static page with Kanban UI at `/`
- [x] Ensure backend serves built frontend assets
- [x] Keep frontend behavior parity with current demo board
- [x] Add/adjust tests for static serving integration

### Tests

- [x] Frontend unit tests: `npm run test:unit`
- [x] Frontend e2e tests: `npm run test:e2e`
- [x] Backend integration test that `/` serves built frontend
- [x] Docker runtime test verifies Kanban loads from container

### Success Criteria

- [x] Visiting `/` in container shows the existing Kanban demo UI
- [x] Unit + e2e + integration tests pass in local workflow

## Part 4 - Fake User Sign-In (Backend Sessions)

### Checklist

- [x] Add backend login endpoint validating only `user` / `password`
- [x] Implement backend session creation and session cookie handling
- [x] Add backend logout endpoint clearing session
- [x] Protect Kanban/API routes behind authenticated session
- [x] Add frontend login screen flow when unauthenticated
- [x] Add frontend logout action and unauthenticated redirect behavior
- [x] Ensure auth checks are backend-enforced (not frontend-only)

### Tests

- [x] `pytest` tests for login success/failure/logout/session-required endpoints
- [x] Frontend unit tests for login form and auth state transitions
- [x] E2E tests for login-required gate and logout flow

### Success Criteria

- [x] Unauthenticated users cannot access protected board APIs
- [x] Authenticated session can access board and survives normal navigation
- [x] Logout fully revokes access until next login

## Part 5 - Database Modeling

### Checklist

- [x] Design SQLite schema for users, boards, and board state
- [x] Store board state as JSON payload linked to `user_id` and `board_id`
- [x] Define migration/init strategy for creating DB if missing
- [x] Define validation rules for board JSON shape
- [x] Document schema and rationale in `docs/`
- [x] Present schema docs to user and get explicit sign-off before backend CRUD implementation

### Tests

- [x] `pytest` tests for DB initialization and schema creation
- [x] `pytest` tests for read/write of board JSON per user/board
- [x] Validation tests for invalid JSON shape rejection

### Success Criteria

- [x] Database schema is documented and approved by user
- [x] Data model supports one board per user now and future extensibility

## Part 6 - Backend Kanban API

### Checklist

- [x] Implement API routes to fetch/update board for authenticated user
- [x] Ensure board records are resolved by authenticated user and board ID
- [x] Create board automatically for a user if first access (or seed default board)
- [x] Persist updates to SQLite JSON payload
- [x] Add request/response models and validation
- [x] Add consistent backend error responses

### Tests

- [x] `pytest` unit tests for service/model validation logic
- [x] `pytest` API tests for authenticated reads/writes
- [x] `pytest` tests for DB auto-create behavior on fresh environment
- [x] `pytest` authorization tests to prevent cross-user access

### Success Criteria

- [x] Backend supports reliable persisted board reads/writes
- [x] APIs are session-protected and user-scoped
- [x] Fresh local run creates DB automatically and works without manual DB setup

## Part 7 - Frontend + Backend Integration

### Checklist

- [x] Replace in-memory board state initialization with backend fetch on load
- [x] Send user actions (rename/add/delete/move) to backend persistence APIs
- [x] Add loading, empty, and error states for API-driven workflow
- [x] Keep UX responsive while syncing server state
- [x] Ensure data reload reflects persisted board state

### Tests

- [x] Frontend unit tests for API client and state transition behavior
- [x] Integration tests with mocked API responses for success/failure
- [x] E2E tests for persistence across refresh
- [x] Backend tests remain green for contract compatibility

### Success Criteria

- [x] Board state persists across page refresh and app restarts
- [x] Frontend no longer depends on hardcoded runtime board state

## Part 8 - AI Connectivity

### Checklist

- [x] Add backend OpenRouter client integration using `OPENROUTER_API_KEY`
- [x] Implement minimal AI route for connectivity checks
- [x] Use `openai/gpt-oss-120b:free` model
- [x] Add secure config/error handling for missing key and provider failures
- [x] Add a controlled "2+2" connectivity test path

### Tests

- [x] `pytest` unit tests with mocked OpenRouter responses
- [x] Optional live integration test (guarded) for "2+2" sanity check
- [x] Error-path tests for missing/invalid API key

### Success Criteria

- [x] Backend can successfully call OpenRouter and return model output
- [x] Connectivity and failure modes are verified and predictable

## Part 9 - Structured Outputs for Kanban Updates

### Checklist

- [x] Define structured output schema with:
  - [x] assistant reply text
  - [x] optional board update operations
- [x] Send current board JSON + user message + conversation history to AI route
- [x] Validate AI structured output strictly on backend
- [x] Apply only valid operations to board model
- [x] Persist validated updates to DB
- [x] Reject/ignore malformed or unsafe operations with clear fallback response
- [x] Add audit-friendly logging for AI request/validation/application flow

### Tests

- [x] `pytest` schema validation tests (valid/invalid/missing fields)
- [x] `pytest` tests for operation application correctness
- [x] `pytest` tests proving backend refuses invalid AI updates
- [x] `pytest` integration tests for successful AI-driven board mutation persistence

### Success Criteria

- [x] AI responses can safely propose board changes
- [x] Backend remains sole authority for validation and persistence
- [x] Invalid AI output cannot corrupt stored board state

## Part 10 - Sidebar AI Chat UX

### Checklist

- [x] Add sidebar chat UI to frontend with conversation history display
- [x] Connect chat UI to backend AI endpoint
- [x] Render assistant reply text from structured output
- [x] Automatically refresh/reconcile board when backend confirms AI-applied updates
- [x] Show pending/error/retry states for chat actions
- [x] Keep interactions accessible and visually aligned with project color scheme

### Tests

- [x] Frontend unit tests for sidebar state, rendering, and API error handling
- [x] Integration tests for chat send/receive cycle with mocked backend
- [x] E2E tests for end-to-end chat plus board auto-refresh behavior
- [x] Regression tests for core Kanban interactions (drag/edit/add/delete)

### Success Criteria

- [x] User can chat with AI in sidebar and receive useful responses
- [x] Valid AI board updates appear in board UI automatically
- [x] Existing Kanban functionality continues to work reliably

## Definition of Done for Entire MVP

- [ ] All part-level success criteria are met in sequence
- [x] Test suites pass (`pytest`, frontend unit, and frontend e2e)
- [x] App runs locally in Docker with backend sessions, persistent board state, and AI-assisted updates