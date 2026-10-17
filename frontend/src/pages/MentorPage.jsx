import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { mentorService } from '../services/mentorService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Bot,
  Send,
  Plus,
  Trash2,
  Sparkles,
  BookOpen,
  User,
  Lightbulb,
  Shield,
  Layers,
  Briefcase,
  TrendingUp,
  Presentation
} from 'lucide-react';

const MENTOR_MODES = [
  { id: 'idea', name: 'Idea Mentor', icon: Lightbulb, desc: 'Sharpen problem significance, clarity, and value proposition.' },
  { id: 'research', name: 'Research Mentor', icon: BookOpen, desc: 'Formulate hypotheses and interpret scholarly literature.' },
  { id: 'technical', name: 'Technical Mentor', icon: Layers, desc: 'Architecture review, database schemas, and API design.' },
  { id: 'product', name: 'Product Mentor', icon: Briefcase, desc: 'MVP scoping, user journeys, and feature prioritization.' },
  { id: 'business', name: 'Business Mentor', icon: TrendingUp, desc: 'Monetization models, unit economics, and market entry.' },
  { id: 'validation', name: 'Validation Mentor', icon: Shield, desc: 'Customer discovery interviews and smoke test design.' },
  { id: 'pitch', name: 'Pitch Mentor', icon: Presentation, desc: 'Slide storytelling, executive summary, and investor Q&A.' },
];

export default function MentorPage() {
  const { id } = useParams();
  const projectId = id ? parseInt(id) : null;
  const { projects, activeProject, setActiveProject } = useProject();

  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedMode, setSelectedMode] = useState('idea');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);

  const selectConversation = async (convId) => {
    try {
      const conv = await mentorService.getConversation(convId);
      setActiveConv(conv);
      setMessages(conv.messages || []);
      setSelectedMode(conv.mode || 'idea');
    } catch (err) {
      console.error("Failed to load conversation:", err);
    }
  };

  const handleNewChat = async (mode = selectedMode) => {
    try {
      const newConv = await mentorService.createConversation({
        project_id: projectId || activeProject?.id,
        mode: mode,
        title: `${MENTOR_MODES.find(m => m.id === mode)?.name || 'Mentor'} Session`
      });
      setConversations(prev => [newConv, ...prev]);
      setActiveConv(newConv);
      setMessages(newConv.messages || []);
      setSelectedMode(mode);
    } catch (err) {
      alert("Failed to initialize mentor conversation.");
    }
  };

  const fetchConversations = async () => {
    try {
      const list = await mentorService.listConversations();
      setConversations(list);
      if (list.length > 0 && !activeConv) {
        selectConversation(list[0].id);
      } else if (list.length === 0) {
        // Start default
        handleNewChat('idea');
      }
    } catch (err) {
      console.error("Error loading mentor chats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeConv) return;

    const userText = inputMessage;
    setInputMessage('');
    // Optimistic user message
    const tempUserMsg = {
      id: Date.now(),
      sender: 'user',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const reply = await mentorService.sendMessage(activeConv.id, userText);
      setMessages((prev) => [...prev, reply]);
    } catch (err) {
      alert("Mentor service is momentarily unavailable.");
    } finally {
      setSending(false);
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (window.confirm("Delete this conversation?")) {
      try {
        await mentorService.deleteConversation(convId);
        const filtered = conversations.filter(c => c.id !== convId);
        setConversations(filtered);
        if (activeConv?.id === convId) {
          if (filtered.length > 0) {
            selectConversation(filtered[0].id);
          } else {
            handleNewChat('idea');
          }
        }
      } catch (err) {
        alert("Failed to delete conversation.");
      }
    }
  };

  const currentModeObj = MENTOR_MODES.find(m => m.id === selectedMode) || MENTOR_MODES[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-5 h-5 text-emerald-400" /> Interactive AI Innovation Mentor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Context-aware pair programming & venture guidance across 7 specialized innovation disciplines.
          </p>
        </div>

        <button
          onClick={() => handleNewChat(selectedMode)}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-md transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> New Session
        </button>
      </div>

      {/* Mode Selector Strip */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {MENTOR_MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = selectedMode === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => {
                setSelectedMode(mode.id);
                handleNewChat(mode.id);
              }}
              className={`px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-all whitespace-nowrap border shrink-0 ${
                isSelected
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{mode.name}</span>
            </button>
          );
        })}
      </div>

      {/* Main Mentor Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[620px]">
        {/* Conversations History Sidebar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col h-full overflow-hidden">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-3 px-1">
            Sessions History
          </span>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`p-2.5 rounded-xl cursor-pointer text-xs flex items-center justify-between group transition-all ${
                  activeConv?.id === conv.id
                    ? 'bg-brand-600/15 border border-brand-500/30 text-white font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Bot className="w-3.5 h-3.5 shrink-0 text-brand-400" />
                  <span className="truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-opacity"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>

          {/* Context pill */}
          {activeProject && (
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300 block truncate">Active Project:</span>
              <span className="truncate block text-brand-400">{activeProject.title}</span>
            </div>
          )}
        </div>

        {/* Chat Window */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-full overflow-hidden shadow-sm">
          {/* Top Chat Bar */}
          <div className="p-3.5 px-5 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <currentModeObj.icon className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white">{activeConv?.title || currentModeObj.name}</h3>
                <p className="text-[10px] text-slate-400">{currentModeObj.desc}</p>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 capitalize">
              Mode: {selectedMode}
            </span>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m, idx) => {
              const isUser = m.sender === 'user';
              return (
                <div key={idx} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className="w-7 h-7 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`max-w-[80%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-brand-600 text-white rounded-tr-none'
                      : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line'
                  }`}>
                    {m.content}

                    {/* Cited sources pill if present */}
                    {m.cited_sources?.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-brand-300">
                        <span className="font-semibold">Linked Project Sources:</span>
                        <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                          {m.cited_sources.map((s, sIdx) => (
                            <li key={sIdx}>{s.title}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 rounded-full bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {sending && (
              <div className="flex gap-3 justify-start">
                <div className="w-7 h-7 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-950 border border-slate-800 rounded-2xl p-3.5 text-xs text-slate-400 flex items-center gap-2">
                  <span className="w-3 h-3 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
                  Synthesizing contextual advice...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input Box */}
          <form onSubmit={handleSendMessage} className="p-3.5 border-t border-slate-800 bg-slate-950/40 flex items-center gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask the ${currentModeObj.name} anything about your architecture, validation, or hypotheses...`}
              className="flex-1 px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              disabled={sending || !inputMessage.trim()}
              className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-40 transition-colors shadow-md"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
