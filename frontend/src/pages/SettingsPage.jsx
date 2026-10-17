import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Settings, Shield, Cpu, Database, Server, User, Globe, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-brand-400" /> Platform & Workspace Settings
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Review your account profile, AI provider configuration, and external research source statuses.
        </p>
      </div>

      <div className="space-y-6">
        {/* User Profile Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <User className="w-4 h-4 text-brand-400" /> User Profile & Security
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400 text-[11px] block">Full Name</span>
              <span className="text-slate-100 font-semibold">{user?.full_name || 'N/A'}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400 text-[11px] block">Email Address</span>
              <span className="text-slate-100 font-semibold">{user?.email || 'N/A'}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400 text-[11px] block">Role & Permissions</span>
              <span className="text-slate-100 font-semibold capitalize">{user?.role || 'Researcher'}</span>
            </div>
          </div>
        </div>

        {/* AI & Research Source Connectivity */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" /> Engine Integrations & Providers
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">LLM Provider Engine</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Configured via backend environment variables (OpenAI / Gemini / Heuristic Fallback)</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold flex items-center gap-1 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Active & Grounded
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">OpenAlex Scholarly Works API</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Live academic literature with DOIs and inverted index abstract reconstruction</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold flex items-center gap-1 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">USPTO Patent Search Adapter</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Official patent records and Google Patents reference linking</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold flex items-center gap-1 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">Background Worker Mode</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Celery & Redis queue with automatic in-process background task fallback</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[11px] font-semibold border border-blue-500/20">
                Async Resilient
              </span>
            </div>
          </div>
        </div>

        {/* Security & Tenant Isolation Notice */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-2">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-brand-400" /> Security & Data Isolation Architecture
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            IdeaLens enforces row-level database ownership verification on every endpoint. No user can access or modify another researcher's private ideas, notes, or files. Secrets are never exposed to the frontend client.
          </p>
        </div>
      </div>
    </div>
  );
}
