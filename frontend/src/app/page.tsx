"use client";

import { useRef, useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const conversationId = useRef(crypto.randomUUID());

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  function startNewConversation() {
    conversationId.current = crypto.randomUUID();
    setMessages([]);
    setMessage("");
  }

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
      const result = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmedMessage,
          conversation_id: conversationId.current,
        }),
      });

      const data = await result.json();

      let assistantMessage = data.reply;

      if (data.error === "llm_rate_limit") {
        assistantMessage =
          "Der KI-Service ist momentan ausgelastet. Bitte versuchen Sie es später erneut.";
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

          {messages.length > 0 && (
            <button
              onClick={startNewConversation}
              className="mt-4 rounded-lg border border-gray-300 bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            >
              Neue Unterhaltung
            </button>
          )}
        </header>

        <div className="flex-1 space-y-4">
          {messages.map((chatMessage, index) => (
            <div
              key={index}
              className={`flex ${
                chatMessage.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  chatMessage.role === "user"
                    ? "bg-gray-900 text-white"
                    : "border border-gray-200 bg-white text-gray-900"
                }`}
              >
                {chatMessage.content}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3 text-gray-500">
                ...
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 py-6">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nachricht schreiben..."
              disabled={isLoading}
              className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none focus:border-gray-500"
            />

            <button
              onClick={sendMessage}
              disabled={isLoading || !message.trim()}
              className="rounded-xl bg-gray-900 px-5 py-3 text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              Senden
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}