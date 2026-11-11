import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  BarChart2,
  Trash2,
  CheckCircle,
  HelpCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  query_plan?: any;
  chart_recommendation?: any;
  verified_metrics?: any;
  suggested_follow_ups?: string[];
  created_at?: string;
}

export const AIAnalystPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [conversationId, setConversationId] = useState<number | undefined>(undefined);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  useEffect(() => {
    if (!activeDataset) return;
    const loadSuggestions = async () => {
      try {
        const suggs = await api.getSuggestions(activeDataset.id);
        setSuggestions(suggs);
      } catch (err) {
        console.error('Failed to load suggestions:', err);
      }
    };
    loadSuggestions();

    // Default welcome message
    setMessages([
      {
        id: 0,
        role: 'assistant',
        content: `Hello! I am your **InsightIQ AI Data Analyst**. I am actively connected to **"${activeDataset.filename}"** (${activeDataset.row_count.toLocaleString()} records).\n\nAsk me any question about your revenue, margins, best/worst performing products, regional breakdowns, or operational trends. Every number I provide is verified through deterministic mathematical computations.`,
        suggested_follow_ups: [
          'What is the total revenue and profit margin?',
          'Which product generated the highest profit?',
          'Compare sales performance across regions',
          'What are the monthly sales trends?',
        ],
      },
    ]);
  }, [activeDataset]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || !activeDataset || isThinking) return;

    const userMsgId = Date.now();
    const newMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: query,
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputQuery('');
    setIsThinking(true);

    try {
      const res = await api.sendChatMessage(activeDataset.id, query, conversationId);
      setConversationId(res.conversation_id);

      const assistantMsg: ChatMessage = {
        id: res.message_id || Date.now() + 1,
        role: 'assistant',
        content: res.answer,
        query_plan: res.query_plan,
        chart_recommendation: res.chart_recommendation,
        verified_metrics: res.verified_metrics,
        suggested_follow_ups: res.suggested_follow_ups,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Failed to send message:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: 'assistant',
          content: 'I encountered an error calculating the analytical query. Please verify backend connection.',
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] bg-[#0f172a] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
      {/* Chat Header Context Banner */}
      <div className="px-6 py-3.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
              <span>AI Data Analyst</span>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded font-medium flex items-center gap-1">
                <ShieldCheck className="w-2.5 h-2.5" /> Verified Math Engine
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Active Context: <span className="text-slate-300 font-semibold">{activeDataset.filename}</span>
            </p>
          </div>
        </div>

        <button
          onClick={clearChat}
          title="Clear Conversation"
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 transition"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-3xl ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gradient-to-tr from-indigo-500 to-cyan-500 text-white'
              }`}
            >
              {msg.role === 'user' ? 'U' : <Sparkles className="w-3.5 h-3.5" />}
            </div>

            {/* Bubble */}
            <div className="space-y-3">
              <div
                className={`p-4 rounded-2xl text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-tr-none'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Computational Plan & Metrics Badge */}
                {msg.query_plan && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
                    <span className="font-semibold text-cyan-400">Operation:</span>
                    <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                      {msg.query_plan.operation}
                    </span>
                  </div>
                )}
              </div>

              {/* Recommended Chart Visualizer */}
              {msg.chart_recommendation?.recommended && msg.chart_recommendation.data?.length > 0 && (
                <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                    <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{msg.chart_recommendation.title}</span>
                  </div>
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      {msg.chart_recommendation.chart_type === 'line' ? (
                        <LineChart data={msg.chart_recommendation.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey={msg.chart_recommendation.x_key} stroke="#64748b" fontSize={10} />
                          <YAxis stroke="#64748b" fontSize={10} />
                          <Tooltip />
                          <Line type="monotone" dataKey={msg.chart_recommendation.y_key} stroke="#6366f1" strokeWidth={2} />
                        </LineChart>
                      ) : (
                        <BarChart data={msg.chart_recommendation.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey={msg.chart_recommendation.x_key} stroke="#64748b" fontSize={10} />
                          <YAxis stroke="#64748b" fontSize={10} />
                          <Tooltip />
                          <Bar dataKey={msg.chart_recommendation.y_key} fill="#06b6d4" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Follow-up question pills */}
              {msg.suggested_follow_ups && msg.suggested_follow_ups.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {msg.suggested_follow_ups.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="text-[11px] px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-indigo-300 hover:border-indigo-500 hover:text-white transition"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading / Thinking Indicator */}
        {isThinking && (
          <div className="flex gap-3 mr-auto max-w-xl">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-500 text-white flex items-center justify-center shrink-0">
              <Sparkles className="w-3.5 h-3.5 animate-spin" />
            </div>
            <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl rounded-tl-none text-xs text-slate-300 flex items-center gap-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce [animation-delay:0.4s]" />
              </div>
              <span className="text-[11px] text-slate-400 ml-1">Computing verified statistics...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      {suggestions.length > 0 && messages.length <= 1 && (
        <div className="px-6 py-2 bg-slate-900/50 border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="text-[11px] text-slate-400 shrink-0">Suggested:</span>
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(s)}
              className="text-[11px] px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 whitespace-nowrap transition"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input Message Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="p-4 bg-slate-900 border-t border-slate-800 flex items-center gap-3"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question about your business data (e.g. 'What is the top product in Europe?')..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white outline-none focus:border-indigo-500 transition"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || isThinking}
          className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white transition flex items-center justify-center shadow-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
