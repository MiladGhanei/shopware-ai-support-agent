"use client";

import { useRef, useState } from "react";
import { Bot, RotateCcw, User } from "lucide-react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const conversationId = useRef(crypto.randomUUID());

  async function sendMessage() {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || isLoading) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: trimmedMessage,
      },
    ]);

    setMessage("");
    setIsLoading(true);

    try {
      const result = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: trimmedMessage,
            conversation_id: conversationId.current,
          }),
        }
      );

      const data = await result.json();

      let assistantMessage = data.reply;

      if (data.error === "llm_rate_limit") {
        assistantMessage =
          "Der KI-Service ist momentan ausgelastet. Bitte versuchen Sie es später erneut.";
      }

      if (data.error === "internal_error") {
        assistantMessage =
          "Entschuldigung, es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.";
      }

      if (!assistantMessage) {
        assistantMessage =
          "Entschuldigung, es ist ein Fehler aufgetreten.";
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: assistantMessage,
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Der Kundenservice ist momentan nicht erreichbar. Bitte versuchen Sie es später erneut.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      sendMessage();
    }
  }

  function startNewConversation() {
    conversationId.current = crypto.randomUUID();
    setMessages([]);
    setMessage("");
  }

  return (
    <main className="min-h-screen bg-gray-50 flex justify-center p-6">
      <div className="flex w-full max-w-2xl flex-col">
        <header className="py-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Kundenservice
          </h1>

          <p className="mt-2 text-gray-500">
            Hallo! Wie können wir Ihnen helfen?
          </p>
        </header>

        <div className="flex-1 space-y-5">
          {messages.map((chatMessage, index) => {
            const isUser = chatMessage.role === "user";

            return (
              <div
                key={index}
                className={`flex items-start gap-3 ${
                  isUser ? "flex-row-reverse" : ""
                }`}
              >
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                    isUser
                      ? "bg-gray-900 text-white"
                      : "border border-gray-200 bg-white text-gray-600"
                  }`}
                >
                  {isUser ? (
                    <User size={18} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>

                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                    isUser
                      ? "bg-gray-900 text-white"
                      : "border border-gray-200 bg-white text-gray-900"
                  }`}
                >
                  {chatMessage.content}
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600">
                <Bot size={18} />
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3 text-gray-500">
                ...
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 py-6">
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={startNewConversation}
                title="Neue Unterhaltung"
                aria-label="Neue Unterhaltung"
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-gray-500 transition hover:bg-gray-100 hover:text-gray-900"
              >
                <RotateCcw size={18} />
              </button>
            )}

            <input
              type="text"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nachricht schreiben..."
              disabled={isLoading}
              className="h-12 flex-1 rounded-xl border border-gray-300 bg-white px-4 text-gray-900 outline-none focus:border-gray-500"
            />

            <button
              onClick={sendMessage}
              disabled={isLoading || !message.trim()}
              className="h-12 rounded-xl bg-gray-900 px-5 text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              Senden
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}