import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanApp } from "@/components/KanbanApp";

const mockFetch = vi.fn<typeof fetch>();

describe("KanbanApp auth flow", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the login form when no session exists", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Unauthorized" }), { status: 401 })
    );

    render(<KanbanApp />);

    expect(await screen.findByRole("heading", { name: /sign in to kanban studio/i })).toBeInTheDocument();
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
  });

  it("logs in and renders the board", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Unauthorized" }), { status: 401 })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<KanbanApp />);

    await screen.findByRole("heading", { name: /sign in to kanban studio/i });
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
    expect(mockFetch).toHaveBeenNthCalledWith(
      2,
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("logs out back to the login screen", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "logged_out" }), { status: 200 }));

    render(<KanbanApp />);

    await screen.findByRole("heading", { name: "Kanban Studio" });
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /sign in to kanban studio/i })).toBeInTheDocument();
    });
  });
});
