import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { mentorService } from '../services/mentorService';
import { useProject } from '../contexts/ProjectContext';
import {
  Bot,
  Send,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  BookOpen,
  User,
  Lightbulb,
  Shield,
  Layers,
  Briefcase,
  TrendingUp,
  Presentation,
  ExternalLink,
  AlertCircle,
  FolderOpen
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
  const { activeProject } = useProject();

  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedMode, setSelectedMode] = useState('idea');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Renaming state
  const [editingConvId, setEditingConvId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const messagesEndRef = useRef(null);

  const selectConversation = async (convId) => {
    setErrorMessage(null);
    try {
      const conv = await mentorService.getConversation(convId);
      setActiveConv(conv);
      setMessages(conv.messages || []);
      setSelectedMode(conv.mode || 'idea');
    } catch (err) {
      console.error("Failed to load conversation:", err);
      setErrorMessage("Failed to load conversation history.");
    }
  };

  const handleNewChat = async (mode = selectedMode) => {
    setErrorMessage(null);
    try {
      const targetModeObj = MENTOR_MODES.find(m => m.id === mode) || MENTOR_MODES[0];
      const newConv = await mentorService.createConversation({
        project_id: projectId || activeProject?.id,
        mode: mode,
        title: `${targetModeObj.name} Session`
      });
      setConversations(prev => [newConv, ...prev.filter(c => c.id !== newConv.id)]);
      setActiveConv(newConv);
      setMessages(newConv.messages || []);
      setSelectedMode(mode);
    } catch (err) {
      console.error("Failed to initialize mentor conversation:", err);
      setErrorMessage("Failed to initialize new mentor session.");
    }
  };

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const list = await mentorService.listConversations();
      setConversations(list);
      if (list.length > 0) {
        // If current activeConv is in list, keep it, else select first
        const currentInList = activeConv ? list.find(c => c.id === activeConv.id) : null;
        if (currentInList) {
          selectConversation(currentInList.id);
        } else {
          selectConversation(list[0].id);
        }
      } else {
        handleNewChat('idea');
      }
    } catch (err) {
      console.error("Error loading mentor chats:", err);
      setErrorMessage("Unable to retrieve mentor conversations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleStartRename = (conv, e) => {
    e.stopPropagation();
    setEditingConvId(conv.id);
    setEditingTitle(conv.title);
  };

  const handleSaveRename = async (convId, e) => {
    e?.stopPropagation();
    if (!editingTitle.trim()) {
      setEditingConvId(null);
      return;
    }
    try {
      const updated = await mentorService.updateConversation(convId, { title: editingTitle.trim() });
      setConversations(prev => prev.map(c => c.id === convId ? { ...c, title: updated.title } : c));
      if (activeConv?.id === convId) {
        setActiveConv(prev => ({ ...prev, title: updated.title }));
      }
      setEditingConvId(null);
    } catch (err) {
      console.error("Failed to rename conversation:", err);
      alert("Failed to update session title.");
    }
  };

  const handleModeChange = async (newMode) => {
    setSelectedMode(newMode);
    if (activeConv) {
      try {
        const targetModeObj = MENTOR_MODES.find(m => m.id === newMode) || MENTOR_MODES[0];
        const updated = await mentorService.updateConversation(activeConv.id, {
          mode: newMode,
          title: activeConv.title.includes('Session') ? `${targetModeObj.name} Session` : activeConv.title
        });
        setActiveConv(updated);
        setConversations(prev => prev.map(c => c.id === updated.id ? { ...c, mode: updated.mode, title: updated.title } : c));
      } catch (err) {
        console.error("Failed to switch mode for active conversation:", err);
      }
    } else {
      handleNewChat(newMode);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeConv || sending) return;

    const userText = inputMessage.trim();
    setInputMessage('');
    setErrorMessage(null);

    // Optimistic user message
    const tempUserMsg = {
      id: Date.now(),
      sender: 'user',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);
    setIsStreaming(true);
    setStreamingText('');

    let streamAccumulator = '';

    try {
      // Attempt SSE streaming
      await mentorService.sendMessageStream(
        activeConv.id,
        userText,
        (chunk) => {
          streamAccumulator += chunk;
          setStreamingText(streamAccumulator);
        },
        (finalMessage) => {
          setIsStreaming(false);
          setStreamingText('');
          if (finalMessage) {
            setMessages((prev) => [...prev, finalMessage]);
          } else if (streamAccumulator) {
            // In case stream ended without full message payload
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now() + 1,
                sender: 'assistant',
                content: streamAccumulator,
                created_at: new Date().toISOString()
              }
            ]);
          }
        },
        async (streamErr) => {
          console.warn("Streaming failed, falling back to standard POST request:", streamErr);
          setIsStreaming(false);
          setStreamingText('');
          // Fallback to standard request
          try {
            const fallbackReply = await mentorService.sendMessage(activeConv.id, userText);
            setMessages((prev) => [...prev, fallbackReply]);
          } catch (postErr) {
            console.error("Standard POST also failed:", postErr);
            setErrorMessage("Mentor service is momentarily unavailable. Please check your AI provider configuration.");
          }
        }
      );
    } catch (err) {
      console.error("Error during message dispatch:", err);
      setErrorMessage("Error sending message. Please try again.");
    } finally {
      setSending(false);
      setIsStreaming(false);
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (window.confirm("Delete this mentor conversation? All messages will be permanently removed.")) {
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

        <div className="flex items-center gap-3">
          {activeProject && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <FolderOpen className="w-3.5 h-3.5 text-brand-400" />
              <span className="text-slate-400">Context:</span>
              <span className="font-semibold text-white max-w-[150px] truncate">{activeProject.title}</span>
            </div>
          )}

          <button
            onClick={() => handleNewChat(selectedMode)}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-md transition-all self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" /> New Session
          </button>
        </div>
      </div>

      {/* Mode Selector Strip */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {MENTOR_MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = selectedMode === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => handleModeChange(mode.id)}
              className={`px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-all whitespace-nowrap border shrink-0 ${
                isSelected
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm font-semibold'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{mode.name}</span>
            </button>
          );
        })}
      </div>

      {/* Error Alert if any */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="p-1 hover:text-rose-200">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Mentor Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[640px]">
        {/* Conversations History Sidebar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col h-full overflow-hidden">
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Sessions History ({conversations.length})
            </span>
            <button
              onClick={() => handleNewChat(selectedMode)}
              className="text-[11px] text-brand-400 hover:text-brand-300 font-semibold flex items-center gap-1"
            >
              <Plus className="w-3 h-3" /> New
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {loading ? (
              <div className="py-8 text-center text-slate-500 text-xs">Loading sessions...</div>
            ) : conversations.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">No active sessions. Start a new one above.</div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`p-2.5 rounded-xl cursor-pointer text-xs flex items-center justify-between group transition-all ${
                    activeConv?.id === conv.id
                      ? 'bg-brand-600/15 border border-brand-500/30 text-white font-semibold'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate flex-1 mr-2">
                    <Bot className="w-3.5 h-3.5 shrink-0 text-brand-400" />
                    {editingConvId === conv.id ? (
                      <div className="flex items-center gap-1 w-full" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(conv.id, e);
                            if (e.key === 'Escape') setEditingConvId(null);
                          }}
                          autoFocus
                          className="w-full bg-slate-950 border border-brand-500 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none"
                        />
                        <button
                          onClick={(e) => handleSaveRename(conv.id, e)}
                          className="p-1 text-emerald-400 hover:text-emerald-300"
                        >
                          <Check className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingConvId(null);
                          }}
                          className="p-1 text-slate-500 hover:text-slate-300"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <span className="truncate">{conv.title}</span>
                    )}
                  </div>

                  {editingConvId !== conv.id && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleStartRename(conv, e)}
                        title="Rename conversation"
                        className="p-1 text-slate-500 hover:text-slate-200 transition-colors"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        title="Delete conversation"
                        className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Context pill */}
          {activeProject && (
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300 block truncate">Active Project Scope:</span>
              <span className="truncate block text-brand-400">{activeProject.title}</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Project context & papers injected automatically</span>
            </div>
          )}
        </div>

        {/* Chat Window */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-full overflow-hidden shadow-sm">
          {/* Top Chat Bar */}
          <div className="p-3.5 px-5 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                <currentModeObj.icon className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-bold text-white">{activeConv?.title || currentModeObj.name}</h3>
                  {activeConv && editingConvId !== activeConv.id && (
                    <button
                      onClick={(e) => handleStartRename(activeConv, e)}
                      title="Rename this conversation"
                      className="text-slate-500 hover:text-slate-300"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
                <p className="text-[10px] text-slate-400">{currentModeObj.desc}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 capitalize font-medium">
                Mode: {selectedMode}
              </span>
            </div>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 && !isStreaming ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                  <currentModeObj.icon className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-white">Welcome to {currentModeObj.name}</h4>
                <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                  {currentModeObj.desc} Ask questions about your architecture, assumptions, literature evidence, or go-to-market strategy.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 max-w-lg w-full text-left">
                  <button
                    onClick={() => setInputMessage(`What are the key technical architectural risks for my project?`)}
                    className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-brand-500/40 text-[11px] text-slate-300 transition-colors"
                  >
                    "What are the key architectural risks?"
                  </button>
                  <button
                    onClick={() => setInputMessage(`How can I conduct lean validation experiments for this idea?`)}
                    className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-brand-500/40 text-[11px] text-slate-300 transition-colors"
                  >
                    "How can I conduct lean validation experiments?"
                  </button>
                </div>
              </div>
            ) : (
              messages.map((m, idx) => {
                const isUser = m.sender === 'user';
                return (
                  <div key={idx} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {!isUser && (
                      <div className="w-7 h-7 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}

                    <div
                      className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed ${
                        isUser
                          ? 'bg-brand-600 text-white rounded-tr-none shadow-md'
                          : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line shadow-sm'
                      }`}
                    >
                      {m.content}

                      {/* Cited sources pill if present */}
                      {m.cited_sources && m.cited_sources.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-slate-800 text-[11px]">
                          <span className="font-semibold text-brand-300 block mb-1">
                            Grounded in Saved Literature & Project Evidence:
                          </span>
                          <div className="space-y-1.5">
                            {m.cited_sources.map((s, sIdx) => (
                              <div
                                key={sIdx}
                                className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between gap-2"
                              >
                                <span className="font-medium text-slate-200 truncate">{s.title || s}</span>
                                {s.source_url && (
                                  <a
                                    href={s.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-brand-400 hover:underline flex items-center gap-1 text-[10px] shrink-0"
                                  >
                                    View <ExternalLink className="w-2.5 h-2.5" />
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
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
              })
            )}

            {/* Live Streaming Message Display */}
            {isStreaming && (
              <div className="flex gap-3 justify-start">
                <div className="w-7 h-7 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="max-w-[80%] rounded-2xl rounded-tl-none p-4 text-xs leading-relaxed bg-slate-950 border border-emerald-500/30 text-slate-200 whitespace-pre-line shadow-sm">
                  {streamingText ? (
                    <div>
                      {streamingText}
                      <span className="inline-block w-1.5 h-3.5 bg-emerald-400 ml-1 animate-pulse" />
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="w-3 h-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                      Connecting to {currentModeObj.name} stream...
                    </div>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Message Input Box */}
          <form
            onSubmit={handleSendMessage}
            className="p-3.5 border-t border-slate-800 bg-slate-950/40 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask the ${currentModeObj.name} anything about hypotheses, stack trade-offs, or validation...`}
              disabled={sending}
              className="flex-1 px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={sending || !inputMessage.trim()}
              className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-40 transition-colors shadow-md shrink-0 flex items-center justify-center"
            >
              {sending ? (
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
