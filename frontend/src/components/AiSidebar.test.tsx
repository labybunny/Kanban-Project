import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AiSidebar } from "@/components/AiSidebar";
import { initialData } from "@/lib/kanban";

const mockFetch = vi.fn<typeof fetch>();

const makeBoardState = () => {
  const cloned = JSON.parse(JSON.stringify(initialData));
  cloned.columns[0].title = "AI Roadmap";
  return cloned;
};

describe("AiSidebar", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends chat message and applies board sync from response", async () => {
    const onBoardStateSync = vi.fn();
    mockFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          model: "arcee-ai/trinity-large-preview:free",
          boardKey: "main",
          assistantResponse: "Updated the board.",
          boardUpdated: true,
          state: makeBoardState(),
          warning: null,
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      )
    );

    render(<AiSidebar onBoardStateSync={onBoardStateSync} />);

    await userEvent.type(
      screen.getByPlaceholderText(/example: move card-1/i),
      "Rename backlog to AI roadmap"
    );
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText("Updated the board.")).toBeInTheDocument();
    expect(onBoardStateSync).toHaveBeenCalledTimes(1);
    expect(onBoardStateSync).toHaveBeenCalledWith(
      expect.objectContaining({
        columns: expect.arrayContaining([
          expect.objectContaining({ id: "col-backlog", title: "AI Roadmap" }),
        ]),
      })
    );
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/ai/chat",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("shows error feedback when AI request fails", async () => {
    const onBoardStateSync = vi.fn();
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "OpenRouter error (500)" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      })
    );

    render(<AiSidebar onBoardStateSync={onBoardStateSync} />);

    await userEvent.type(screen.getByPlaceholderText(/example: move card-1/i), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText(/openrouter error/i)).toBeInTheDocument();
    expect(await screen.findByText(/i could not process that request right now/i)).toBeInTheDocument();
    expect(onBoardStateSync).not.toHaveBeenCalled();
  });

  it("keeps the message viewport fixed height", () => {
    render(<AiSidebar onBoardStateSync={vi.fn()} />);

    expect(screen.getByTestId("ai-chat-messages")).toHaveClass("h-44");
  });
});
