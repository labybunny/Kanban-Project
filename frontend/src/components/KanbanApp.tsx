"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";
import {
  ApiError,
  getBoard,
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  updateBoard,
} from "@/lib/api";

type AuthStatus = "loading" | "unauthenticated" | "authenticated";
type BoardStatus = "loading" | "ready" | "error";

const emptyCredentials = { username: "", password: "" };

export const KanbanApp = () => {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [boardStatus, setBoardStatus] = useState<BoardStatus>("loading");
  const [credentials, setCredentials] = useState(emptyCredentials);
  const [activeUser, setActiveUser] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [boardError, setBoardError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [initialBoard, setInitialBoard] = useState<BoardData | null>(null);

  const loadBoard = useCallback(async () => {
    setBoardStatus("loading");
    setBoardError(null);

    try {
      const boardPayload = await getBoard("main");
      setInitialBoard(boardPayload.state);
      setBoardStatus("ready");
    } catch (caughtError) {
      if (caughtError instanceof ApiError && caughtError.status === 401) {
        setActiveUser(null);
        setStatus("unauthenticated");
        setBoardStatus("loading");
        return;
      }

      setBoardError("Unable to load board. Please retry.");
      setBoardStatus("error");
    }
  }, []);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const data = await getCurrentUser();
        setActiveUser(data.username);
        setStatus("authenticated");
        await loadBoard();
      } catch (caughtError) {
        if (caughtError instanceof ApiError && caughtError.status === 401) {
          setStatus("unauthenticated");
          return;
        }

        setError("Unable to reach the server. Try again.");
        setStatus("unauthenticated");
      }
    };

    void checkSession();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const data = await loginRequest(credentials.username, credentials.password);
      setCredentials(emptyCredentials);
      setActiveUser(data.username);
      setStatus("authenticated");
      await loadBoard();
    } catch (caughtError) {
      if (caughtError instanceof ApiError && caughtError.status === 401) {
        setError("Invalid credentials. Use user / password.");
        setStatus("unauthenticated");
        return;
      }

      setError("Unable to reach the server. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      await logoutRequest();
    } finally {
      setIsSubmitting(false);
      setActiveUser(null);
      setInitialBoard(null);
      setBoardStatus("loading");
      setBoardError(null);
      setSyncError(null);
      setStatus("unauthenticated");
    }
  };

  const persistBoard = useCallback(async (nextBoard: BoardData) => {
    setIsSaving(true);
    setSyncError(null);

    try {
      await updateBoard(nextBoard, "main");
    } catch (caughtError) {
      if (caughtError instanceof ApiError && caughtError.status === 401) {
        setActiveUser(null);
        setInitialBoard(null);
        setBoardStatus("loading");
        setStatus("unauthenticated");
        return;
      }
      setSyncError("Could not save changes. A refresh may lose recent edits.");
    } finally {
      setIsSaving(false);
    }
  }, []);

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <div className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <h1 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Kanban Studio
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">Checking session...</p>
        </div>
      </main>
    );
  }

  if (status === "unauthenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Project Management MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in to Kanban Studio
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">
            Use the demo credentials to continue.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" data-testid="login-form">
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                Username
              </span>
              <input
                value={credentials.username}
                onChange={(event) =>
                  setCredentials((prev) => ({ ...prev, username: event.target.value }))
                }
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
                required
              />
            </label>

            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                Password
              </span>
              <input
                type="password"
                value={credentials.password}
                onChange={(event) =>
                  setCredentials((prev) => ({ ...prev, password: event.target.value }))
                }
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
                required
              />
            </label>

            {error ? (
              <p className="rounded-xl border border-[var(--accent-yellow)] bg-[rgba(236,173,10,0.08)] px-3 py-2 text-sm text-[var(--navy-dark)]">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  if (boardStatus === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <h1 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Kanban Studio
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">
            {boardError ?? "Unable to load board."}
          </p>
          <div className="mt-6 flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                void loadBoard();
              }}
              className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={() => {
                void handleLogout();
              }}
              className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
            >
              Log out
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (boardStatus === "loading" || !initialBoard) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <h1 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Kanban Studio
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">Loading board...</p>
          <div className="mt-5">
            <button
              type="button"
              onClick={() => {
                void handleLogout();
              }}
              className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
            >
              Log out
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <KanbanBoard
      username={activeUser ?? undefined}
      onLogout={handleLogout}
      initialBoard={initialBoard}
      onBoardPersist={persistBoard}
      isSaving={isSaving}
      syncError={syncError}
    />
  );
};
