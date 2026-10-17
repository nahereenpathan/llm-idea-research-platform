import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useProject } from '../../contexts/ProjectContext';
import { Sparkles, LogOut, Folder, PlusCircle, User, Shield } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { projects, activeProject, setActiveProject } = useProject();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                IdeaLens <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 font-medium">AI Platform</span>
              </span>
            </div>
          </Link>

          {/* Active Project Switcher */}
          {projects.length > 0 && (
            <div className="hidden md:flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <Folder className="w-4 h-4 text-brand-400" />
              <select
                className="bg-transparent text-sm text-slate-200 focus:outline-none cursor-pointer pr-2"
                value={activeProject?.id || ''}
                onChange={(e) => {
                  const sel = projects.find((p) => p.id === parseInt(e.target.value));
                  if (sel) setActiveProject(sel);
                }}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id} className="bg-slate-900 text-slate-100">
                    {p.title}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* User actions */}
        <div className="flex items-center gap-3">
          <Link
            to="/projects"
            className="hidden sm:flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-brand-400" />
            New Project
          </Link>

          <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-brand-400 text-sm font-semibold">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="hidden lg:block text-left text-xs">
              <p className="font-medium text-slate-200 truncate max-w-[120px]">{user?.full_name || user?.email}</p>
              <p className="text-slate-400 text-[10px] capitalize">{user?.role || 'Researcher'}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors ml-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
