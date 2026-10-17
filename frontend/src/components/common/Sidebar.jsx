import React from 'react';
import { NavLink } from 'react-router-dom';
import { useProject } from '../../contexts/ProjectContext';
import {
  LayoutDashboard,
  GitCompare,
  BookOpen,
  Search,
  Split,
  Milestone,
  Bot,
  FileText,
  Presentation,
  FolderKanban,
  Settings
} from 'lucide-react';

export default function Sidebar() {
  const { activeProject } = useProject();
  const projectId = activeProject?.id;

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
    { label: 'Idea Comparison', icon: GitCompare, to: projectId ? `/projects/${projectId}/compare` : '/projects', badge: activeProject ? null : 'Pick project' },
    { label: 'Research Papers', icon: BookOpen, to: projectId ? `/projects/${projectId}/research` : '/projects' },
    { label: 'Patent Search', icon: Search, to: projectId ? `/projects/${projectId}/patents` : '/projects' },
    { label: 'Research Gaps', icon: Split, to: projectId ? `/projects/${projectId}/gaps` : '/projects' },
    { label: 'Roadmap & Tasks', icon: Milestone, to: projectId ? `/projects/${projectId}/roadmap` : '/projects' },
    { label: 'AI Mentor', icon: Bot, to: projectId ? `/projects/${projectId}/mentor` : '/mentor' },
    { label: 'Reports & Docs', icon: FileText, to: projectId ? `/projects/${projectId}/reports` : '/projects' },
    { label: 'Presentation Builder', icon: Presentation, to: projectId ? `/projects/${projectId}/presentations` : '/projects' },
    { label: 'All Projects', icon: FolderKanban, to: '/projects' },
    { label: 'Settings', icon: Settings, to: '/settings' }
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 border-b border-slate-800/80">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Workflow Workspace</p>
        <p className="text-sm font-medium text-slate-200 truncate mt-0.5">
          {activeProject ? activeProject.title : 'No active project selected'}
        </p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600/15 text-brand-400 border border-brand-500/20 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Workflow Phase Indicator */}
      <div className="p-4 m-3 rounded-xl bg-slate-800/40 border border-slate-800 text-xs text-slate-400">
        <p className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Engine Active
        </p>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          OpenAlex, USPTO, and explainable 10-dimension evaluation ready.
        </p>
      </div>
    </aside>
  );
}
