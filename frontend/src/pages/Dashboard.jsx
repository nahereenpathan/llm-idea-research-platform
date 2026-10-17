import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  FolderKanban,
  Lightbulb,
  FileCheck,
  Activity,
  ArrowRight,
  GitCompare,
  BookOpen,
  Search,
  Bot,
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { activeProject, setActiveProject, projects } = useProject();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await projectService.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to load dashboard metrics:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const projectId = activeProject?.id;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-navy-900 to-slate-900 border border-slate-800 p-6 md:p-8">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-medium mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse"></span>
            IdeaLens Innovation Intelligence
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Research, Evaluate, and Validate Your Next Big Idea
          </h1>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            Submit up to 3 candidate ideas for 10-dimension explainable scoring, search real academic papers and patents,
            identify research gaps, and generate exportable presentations and roadmaps.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-5">
            <Link
              to={projectId ? `/projects/${projectId}/compare` : '/projects'}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/20 transition-all"
            >
              <GitCompare className="w-4 h-4" /> Compare Ideas
            </Link>
            <Link
              to={projectId ? `/projects/${projectId}/research` : '/projects'}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors"
            >
              <BookOpen className="w-4 h-4 text-brand-400" /> Academic Search
            </Link>
            <Link
              to={projectId ? `/projects/${projectId}/mentor` : '/mentor'}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors"
            >
              <Bot className="w-4 h-4 text-emerald-400" /> Open AI Mentor
            </Link>
          </div>
        </div>
      </div>

      {/* Real Statistics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Projects</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <FolderKanban className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-3">
            {loading ? '...' : stats?.total_projects || 0}
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">Active user workspaces</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Ideas Analyzed</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Lightbulb className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-3">
            {loading ? '...' : stats?.ideas_analyzed || 0}
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">10-dimension evaluations</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Reports Generated</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <FileCheck className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-3">
            {loading ? '...' : stats?.reports_generated || 0}
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">Exported PDF/DOCX/TeX</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Research Engines</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-3">Active</p>
          <span className="text-[11px] text-emerald-400 mt-1 block font-medium">OpenAlex & USPTO live</span>
        </div>
      </div>

      {/* Two Column Layout: Recent Projects & Active Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Your Research Projects</h2>
              <p className="text-xs text-slate-400">Select or continue working on an idea project</p>
            </div>
            <Link
              to="/projects"
              className="text-xs font-medium text-brand-400 hover:text-brand-300 flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {stats?.recent_projects?.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-slate-800 rounded-xl">
              <FolderKanban className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm text-slate-400 font-medium">No projects created yet</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Create a project to submit up to 3 candidate ideas for comparative analysis and patent research.
              </p>
              <Link
                to="/projects"
                className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium"
              >
                <Plus className="w-3.5 h-3.5" /> Create First Project
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {stats?.recent_projects?.map((proj) => (
                <div
                  key={proj.id}
                  onClick={() => {
                    const full = projects.find((p) => p.id === proj.id);
                    if (full) setActiveProject(full);
                    navigate(`/projects/${proj.id}/compare`);
                  }}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                    activeProject?.id === proj.id
                      ? 'bg-slate-800/80 border-brand-500/40 shadow-sm'
                      : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700 hover:bg-slate-850'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-white">{proj.title}</h3>
                      {activeProject?.id === proj.id && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/30">
                          Active Workspace
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>{proj.domain || 'General Technology'}</span>
                      <span>•</span>
                      <span>{proj.ideas_count} idea(s) submitted</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 group-hover:text-white">
                    <span>Open Workflow</span>
                    <ArrowRight className="w-4 h-4 text-brand-400" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Research Jobs / Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-400" /> Research Jobs
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Real-time</span>
          </div>

          <div className="flex-1 space-y-3">
            {stats?.recent_jobs?.length === 0 ? (
              <div className="text-center py-10 border border-dashed border-slate-800 rounded-xl my-auto">
                <Clock className="w-7 h-7 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400">No background jobs currently running.</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Searches and exports run with progress tracking.
                </p>
              </div>
            ) : (
              stats?.recent_jobs?.map((job) => (
                <div key={job.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-200 capitalize">
                      {job.job_type.replace('_', ' ')}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" /> {job.status}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-brand-500 h-full rounded-full transition-all"
                      style={{ width: `${job.progress_percentage || 100}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 truncate">{job.status_message}</p>
                </div>
              ))
            )}
          </div>

          {/* Quick Start Guidance */}
          <div className="mt-5 pt-4 border-t border-slate-800 text-xs text-slate-400 space-y-2">
            <p className="font-semibold text-slate-300">Quick Start Flow:</p>
            <ol className="list-decimal list-inside space-y-1 text-[11px]">
              <li>Create a project and submit 1 to 3 ideas.</li>
              <li>Run 10-dimension evaluation with weight sliders.</li>
              <li>Query OpenAlex and USPTO for prior art.</li>
              <li>Generate gap reports, roadmap, and presentation.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
