# Frontend Code Guide

## Purpose

This directory contains the Next.js frontend for the Project Management MVP.
It is exported as static assets and served by the FastAPI backend.

## Stack and Tooling

- Next.js (App Router) with React + TypeScript
- Tailwind CSS v4 for styling (`src/app/globals.css`)
- `@dnd-kit` for drag-and-drop interactions
- Testing:
  - Unit/component: Vitest + React Testing Library
  - End-to-end: Playwright

## Current App Behavior

- `/` renders `KanbanApp` (`src/app/page.tsx`)
- On first load, frontend checks session via `GET /api/auth/me`
- Unauthenticated users are shown a login form and must sign in with `user` / `password`
- Authenticated users see the Kanban board and can log out
- The board has five columns with editable titles
- Cards can be:
  - reordered within a column
  - moved across columns via drag-and-drop
  - created from the "Add a card" form
  - removed with the card action button
- All board state is in-memory in React state, initialized from `initialData`

## Key Files

- `src/app/layout.tsx`
  - Global app shell and font setup
- `src/app/page.tsx`
  - Entry page that renders `KanbanApp`
- `src/app/globals.css`
  - Theme variables and base styles (includes project color palette)
- `src/components/KanbanApp.tsx`
  - Auth gate and login form
  - Session check (`/api/auth/me`) and login/logout API calls
- `src/components/KanbanBoard.tsx`
  - Top-level board state, drag lifecycle, rename/add/delete handlers
  - Shows signed-in user and logout action when authenticated
- `src/components/KanbanColumn.tsx`
  - Column UI, droppable container, title input, card list, new-card form
- `src/components/KanbanCard.tsx`
  - Sortable card item and remove action
- `src/components/NewCardForm.tsx`
  - Expandable add-card form with validation for non-empty title
- `src/components/KanbanCardPreview.tsx`
  - Drag overlay preview card
- `src/lib/kanban.ts`
  - Core types (`Card`, `Column`, `BoardData`), seed data, `moveCard`, `createId`

## Test Files

- `src/lib/kanban.test.ts`
  - Unit tests for `moveCard` logic
- `src/components/KanbanBoard.test.tsx`
  - Component behavior tests (render, rename, add/remove)
- `src/components/KanbanApp.test.tsx`
  - Auth UI tests (unauthenticated state, login success, logout flow)
- `tests/kanban.spec.ts`
  - Browser tests for login gate, board interactions, and logout flow
- `vitest.config.ts`, `src/test/setup.ts`, `playwright.config.ts`
  - Test runner configuration

## Commands

From `frontend/`:

- Install: `npm install`
- Dev server: `npm run dev`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- Full tests: `npm run test:all`

## Constraints for Future Work

- Keep behavior simple and aligned with the MVP scope
- Prefer small, focused changes that preserve current UX
- Maintain test coverage for core card and column interactions
- Keep backend as source of truth for authentication and future board persistence
