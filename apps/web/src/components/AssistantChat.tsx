'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Loader2 } from 'lucide-react';
import { assistantAPI } from '@/lib/api';
import { cn } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SUGGESTIONS = [
  'What are the most critical incidents right now?',
  'Which rescue resources are available near Colombo?',
  'Summarize active hazards and blocked routes',
  'How many incidents need human approval?',
];

export function AssistantChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'I am the ResQGrid AI Command Assistant. Ask me about incidents, resources, hazards, or recommendations.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: text.trim(), timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const { data } = await assistantAPI.query(userMsg.content);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer, timestamp: new Date(data.timestamp) },
      ]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: typeof detail === 'string' ? detail : 'Sorry, I could not process that request.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-40 flex flex-col items-end">
      {isOpen && (
        <div className="mb-3 w-80 sm:w-96 rounded-2xl border border-command-border bg-command-panel/95 backdrop-blur-md shadow-2xl overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-command-border bg-command-bg/60">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-600 to-fuchsia-500 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-200">AI Command Assistant</p>
                <p className="text-[10px] text-slate-500">Human-in-the-loop decision support</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg hover:bg-command-raised text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="h-80 overflow-y-auto p-3 space-y-3 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={cn(
                  'flex gap-2',
                  msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                <div
                  className={cn(
                    'w-6 h-6 rounded-full shrink-0 flex items-center justify-center',
                    msg.role === 'user' ? 'bg-blue-500/20 text-blue-400' : 'bg-violet-500/20 text-violet-400'
                  )}
                >
                  {msg.role === 'user' ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                </div>
                <div
                  className={cn(
                    'max-w-[80%] rounded-xl px-3 py-2 text-xs leading-relaxed',
                    msg.role === 'user'
                      ? 'bg-blue-600/20 text-blue-100 border border-blue-500/25'
                      : 'bg-command-raised text-slate-300 border border-command-border'
                  )}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-violet-500/20 text-violet-400 shrink-0 flex items-center justify-center">
                  <Bot className="w-3 h-3" />
                </div>
                <div className="rounded-xl px-3 py-2 bg-command-raised border border-command-border flex items-center gap-2">
                  <Loader2 className="w-3 h-3 animate-spin text-violet-400" />
                  <span className="text-xs text-slate-400">Analyzing situation…</span>
                </div>
              </div>
            )}

            {messages.length <= 1 && !loading && (
              <div className="space-y-1.5 pt-1">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Suggested questions</p>
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="block w-full text-left text-[11px] text-slate-400 hover:text-slate-200 bg-command-bg/40 hover:bg-command-bg border border-command-borderhover/50 hover:border-slate-600 rounded-lg px-2.5 py-1.5 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="p-3 border-t border-command-border bg-command-bg/60"
          >
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about incidents, resources, hazards…"
                className="flex-1 bg-command-bg border border-command-borderhover/60 rounded-xl px-3 py-2 text-xs placeholder:text-slate-600 focus:outline-none focus:border-violet-500/60 focus:ring-2 focus:ring-violet-500/20 transition-all"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="p-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-500 text-white disabled:opacity-40 transition-all hover:shadow-lg hover:shadow-violet-500/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-4 py-3 rounded-full shadow-2xl text-white text-sm font-semibold transition-all hover:scale-105 active:scale-95',
          isOpen
            ? 'bg-slate-700 hover:bg-slate-600'
            : 'bg-gradient-to-r from-violet-600 to-fuchsia-500 hover:shadow-violet-500/30'
        )}
      >
        {isOpen ? (
          <>
            <X className="w-4 h-4" /> Close Assistant
          </>
        ) : (
          <>
            <MessageSquare className="w-4 h-4" /> Ask AI Assistant
          </>
        )}
      </button>
    </div>
  );
}
