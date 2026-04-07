import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  messages: Message[];
}

const API_URL = '/api/chat';
const HEALTH_URL = '/api/chat/health';
const STORAGE_KEYS = ['korgen_chat_sessions', 'parkguard_chat_sessions'] as const;
const STORAGE_KEY = STORAGE_KEYS[0];
const MAX_SESSIONS = 50;

const QUICK_QUESTIONS = [
  'How many violations were created today?',
  'How many active alarms are open now?',
  'Which plates violate most often?',
  'Which camera is the busiest?',
  'Create a short summary for today.',
];

const WELCOME_MESSAGE: Message = {
  id: 0,
  role: 'assistant',
  content: 'Korgen Vision assistant is ready. Ask about alarms, cameras, plates, reports, or system status.',
};

function loadSessions(): ChatSession[] {
  for (const key of STORAGE_KEYS) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;

      const sessions: ChatSession[] = JSON.parse(raw);
      return sessions.map((session) => ({
        ...session,
        messages: session.messages.map((message) => ({
          ...message,
          streaming: false,
        })),
      }));
    } catch {
      continue;
    }
  }

  return [];
}

function saveSessions(sessions: ChatSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)));
  } catch {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, 10)));
    } catch {
      // noop
    }
  }
}

function createSession(): ChatSession {
  return {
    id: crypto.randomUUID(),
    title: 'New chat',
    createdAt: new Date().toISOString(),
    messages: [{ ...WELCOME_MESSAGE }],
  };
}

function makeSessionTitle(text: string) {
  return text.length > 40 ? `${text.slice(0, 40)}...` : text;
}

function formatSessionDate(iso: string) {
  const date = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / 86400000);

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';

  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
  });
}

export default function ChatPanel() {
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions);
  const [activeId, setActiveId] = useState<string | null>(() => loadSessions()[0]?.id ?? null);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const msgIdRef = useRef(1);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeId) ?? null,
    [activeId, sessions]
  );

  useEffect(() => {
    fetch(HEALTH_URL)
      .then((res) => res.json())
      .then((data) => setOllamaOk(Boolean(data?.ok)))
      .catch(() => setOllamaOk(false));
  }, []);

  useEffect(() => {
    saveSessions(sessions);
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions]);

  const updateSession = useCallback((id: string, updater: (session: ChatSession) => ChatSession) => {
    setSessions((prev) => prev.map((session) => (session.id === id ? updater(session) : session)));
  }, []);

  const handleStartNew = () => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveId(session.id);
    setInput('');
    inputRef.current?.focus();
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => {
      const next = prev.filter((session) => session.id !== id);
      if (activeId === id) {
        setActiveId(next[0]?.id ?? null);
      }
      return next;
    });
  };

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || streaming) return;

    let sessionId = activeId;
    if (!sessionId) {
      const session = createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveId(session.id);
      sessionId = session.id;
    }

    const sessionBefore = sessions.find((session) => session.id === sessionId);
    const history = (sessionBefore?.messages ?? [])
      .filter((message) => !message.streaming && message.id !== 0)
      .map((message) => ({ role: message.role, content: message.content }));

    const userMessage: Message = {
      id: msgIdRef.current++,
      role: 'user',
      content: trimmed,
    };
    const assistantId = msgIdRef.current++;
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
    };
    const isFirstUserMessage = !history.some((message) => message.role === 'user');

    setInput('');
    setStreaming(true);

    updateSession(sessionId, (session) => ({
      ...session,
      title: isFirstUserMessage ? makeSessionTitle(trimmed) : session.title,
      messages: [...session.messages, userMessage, assistantMessage],
    }));

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...history, { role: 'user', content: trimmed }],
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        setSessions((prev) =>
          prev.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  messages: session.messages.map((message) =>
                    message.id === assistantId
                      ? { ...message, content: message.content + chunk }
                      : message
                  ),
                }
              : session
          )
        );
      }

      setSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                messages: session.messages.map((message) =>
                  message.id === assistantId
                    ? { ...message, streaming: false }
                    : message
                ),
              }
            : session
        )
      );
      setOllamaOk(true);
    } catch {
      setSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                messages: session.messages.map((message) =>
                  message.id === assistantId
                    ? {
                        ...message,
                        content: '[Backend chat or Ollama is unavailable]',
                        streaming: false,
                      }
                    : message
                ),
              }
            : session
        )
      );
      setOllamaOk(false);
    } finally {
      setStreaming(false);
      inputRef.current?.focus();
    }
  }, [activeId, sessions, streaming, updateSession]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(input);
    }
  };

  const messages = activeSession?.messages ?? [];

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {sidebarOpen && (
        <div className="w-64 flex-shrink-0 flex flex-col border-r border-gray-800 bg-gray-950">
          <div className="px-3 py-3 border-b border-gray-800 flex items-center gap-2">
            <button
              onClick={handleStartNew}
              className="flex-1 flex items-center gap-2 bg-blue-700 hover:bg-blue-600 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
            >
              <span className="text-lg leading-none">+</span>
              New chat
            </button>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-500 hover:text-gray-300 text-lg px-1"
              title="Hide"
            >
              &lsaquo;
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-2">
            {sessions.length === 0 && (
              <p className="text-xs text-gray-600 text-center mt-6 px-3">
                No history yet.
              </p>
            )}
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => setActiveId(session.id)}
                className={`group mx-2 mb-1 px-3 py-2 rounded-lg cursor-pointer flex items-start gap-2 transition-colors ${
                  session.id === activeId
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-base mt-0.5 flex-shrink-0">#</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate">{session.title}</div>
                  <div className="text-xs text-gray-600 mt-0.5">
                    {formatSessionDate(session.createdAt)}
                  </div>
                </div>
                <button
                  onClick={(event) => {
                    event.stopPropagation();
                    handleDeleteSession(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 text-xs flex-shrink-0 transition-all"
                  title="Delete"
                >
                  x
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 flex-shrink-0">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-gray-500 hover:text-gray-300 text-lg mr-1"
              title="Show history"
            >
              &rsaquo;
            </button>
          )}
          <img src="/korgen-icon.svg" alt="KV" className="w-8 h-8 flex-shrink-0" />
          <div className="min-w-0">
            <div className="font-semibold text-sm text-white truncate">
              {activeSession?.title ?? 'Korgen Vision Assistant'}
            </div>
            <div className="text-xs text-gray-400">Korgen Vision AI</div>
          </div>
          <div className="ml-auto flex items-center gap-1.5 flex-shrink-0">
            <div
              className={`w-2 h-2 rounded-full ${
                ollamaOk === true ? 'bg-green-500' : ollamaOk === false ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
              }`}
            />
            <span className="text-xs text-gray-400">
              {ollamaOk === true ? 'Online' : ollamaOk === false ? 'Offline' : '...'}
            </span>
          </div>
        </div>

        <div className="px-4 py-2 border-b border-gray-800 flex gap-2 flex-wrap flex-shrink-0">
          {QUICK_QUESTIONS.map((question) => (
            <button
              key={question}
              onClick={() => void sendMessage(question)}
              disabled={streaming}
              className="text-xs bg-gray-800 hover:bg-blue-900 hover:text-blue-200 text-gray-300 px-3 py-1 rounded-full transition-colors border border-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {question}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-3">
              <img src="/korgen-icon.svg" alt="KV" className="w-14 h-14" />
              <p className="text-sm">Start a new chat to ask the assistant.</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <img src="/korgen-icon.svg" alt="KV" className="w-7 h-7 mr-2 mt-1 flex-shrink-0" />
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-gray-800 text-gray-100 rounded-bl-sm'
                }`}
              >
                {message.streaming && !message.content && (
                  <span className="inline-flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                )}
                {message.content}
                {message.streaming && message.content && (
                  <span className="inline-block w-0.5 h-4 bg-gray-300 ml-0.5 animate-pulse align-text-bottom" />
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="px-4 py-3 border-t border-gray-800 flex-shrink-0">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={streaming}
              placeholder={ollamaOk === false ? 'Chat backend is offline...' : 'Type a message...'}
              className="flex-1 bg-gray-800 text-white placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm border border-gray-700 focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            />
            <button
              onClick={() => void sendMessage(input)}
              disabled={!input.trim() || streaming}
              className="bg-blue-700 hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors"
            >
              {streaming ? '...' : 'Send'}
            </button>
          </div>
          <div className="text-xs text-gray-600 mt-1.5 text-center">
            Enter to send. Session history is stored locally.
          </div>
        </div>
      </div>
    </div>
  );
}
