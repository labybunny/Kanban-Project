import type { BoardData } from "@/lib/kanban";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const parseJsonSafely = async <T>(response: Response): Promise<T | null> => {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }
  return (await response.json()) as T;
};

const requestJson = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, init);
  const payload = await parseJsonSafely<T | { detail?: string }>(response);

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload.detail ?? "Request failed")
        : "Request failed";
    throw new ApiError(detail, response.status);
  }

  if (payload === null) {
    throw new ApiError("Expected JSON response", response.status);
  }
  return payload as T;
};

export const getCurrentUser = async (): Promise<{ username: string }> =>
  requestJson<{ username: string }>("/api/auth/me");

export const login = async (
  username: string,
  password: string
): Promise<{ username: string }> =>
  requestJson<{ username: string }>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

export const logout = async (): Promise<{ status: string }> =>
  requestJson<{ status: string }>("/api/auth/logout", { method: "POST" });

export const getBoard = async (
  boardKey = "main"
): Promise<{ boardKey: string; state: BoardData }> =>
  requestJson<{ boardKey: string; state: BoardData }>(`/api/boards/${boardKey}`);

export const updateBoard = async (
  state: BoardData,
  boardKey = "main"
): Promise<{ boardKey: string; state: BoardData }> =>
  requestJson<{ boardKey: string; state: BoardData }>(`/api/boards/${boardKey}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });
