"use client";

import { useMemo, useState, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";
import { ApiError, chatWithAi, type ChatHistoryTurn } from "@/lib/api";

type AiSidebarProps = {
  onBoardStateSync: (nextBoard: BoardData) => void;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  warning?: string | null;
};

export const AiSidebar = ({ onBoardStateSync }: AiSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Ask me to plan, add, move, rename, or tidy cards on your board.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const history = useMemo<ChatHistoryTurn[]>(
    () =>
      messages.map((message) => ({
        role: message.role,
        content: message.content,
      })),
    [messages]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }

    setError(null);
    setIsSending(true);
    setInput("");
    setMessages((previous) => [...previous, { role: "user", content: trimmed }]);

    try {
      const response = await chatWithAi(trimmed, history);
      onBoardStateSync(response.state);
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: response.assistantResponse,
          warning: response.warning,
        },
      ]);
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError("Unable to reach AI service right now.");
      }
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: "I could not process that request right now.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex h-full min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-white p-5 shadow-[var(--shadow)]">
      <div className="border-b border-[var(--stroke)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
          Board Copilot
        </h2>
        <p className="mt-2 text-sm text-[var(--gray-text)]">
          Ask for board updates in plain language.
        </p>
      </div>

      <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1" data-testid="ai-chat-messages">
        {messages.map((message, index) => (
          <article
            key={`${message.role}-${index}-${message.content.slice(0, 16)}`}
            className={
              message.role === "user"
                ? "ml-10 rounded-2xl bg-[var(--secondary-purple)] px-3 py-2 text-sm text-white"
                : "mr-10 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            <p className="whitespace-pre-wrap leading-6">{message.content}</p>
            {message.warning ? (
              <p className="mt-2 rounded-lg bg-[rgba(236,173,10,0.14)] px-2 py-1 text-xs font-semibold text-[var(--navy-dark)]">
                {message.warning}
              </p>
            ) : null}
          </article>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3" data-testid="ai-chat-form">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Example: Move card-1 to Review and rename Backlog to Roadmap."
          rows={3}
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          disabled={isSending}
        />
        {error ? (
          <p className="rounded-xl border border-[var(--accent-yellow)] bg-[rgba(236,173,10,0.08)] px-3 py-2 text-xs font-semibold text-[var(--navy-dark)]">
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSending}
        >
          {isSending ? "Sending..." : "Send to AI"}
        </button>
      </form>
    </aside>
  );
};
