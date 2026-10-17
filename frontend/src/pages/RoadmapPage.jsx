import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { roadmapService } from '../services/roadmapService';
import { ideaService } from '../services/ideaService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Milestone,
  Sparkles,
  CheckCircle2,
  Clock,
  Layers,
  Database,
  Server,
  Code2,
  ShieldCheck,
  AlertCircle,
  Calendar,
  CheckSquare,
  Square
} from 'lucide-react';

export default function RoadmapPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('milestones'); // 'milestones', 'tasks', 'architecture'

  const fetchData = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);

      const ideasList = await ideaService.listIdeas(projectId);
      setIdeas(ideasList);
      const active = ideasList.find((i) => i.is_selected) || ideasList[0];
      if (active) setSelectedIdeaId(active.id);

      const roadmaps = await roadmapService.getRoadmaps(projectId);
      if (roadmaps.length > 0) {
        setRoadmap(roadmaps[0]);
      }
    } catch (err) {
      console.error("Error loading roadmap data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleGenerate = async () => {
    if (!selectedIdeaId) return;
    setGenerating(true);
    try {
      const res = await roadmapService.generateRoadmap(projectId, selectedIdeaId);
      setRoadmap(res);
    } catch (err) {
      alert("Failed to generate implementation roadmap.");
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleTaskStatus = async (taskId, currentStatus) => {
    const nextStatus = currentStatus === 'done' ? 'todo' : currentStatus === 'todo' ? 'in_progress' : 'done';
    try {
      const updated = await roadmapService.updateTaskStatus(projectId, taskId, nextStatus);
      setRoadmap(updated);
    } catch (err) {
      alert("Failed to update task status.");
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400 flex items-center justify-center gap-2">
        <span className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        Loading implementation blueprint...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Milestone className="w-5 h-5 text-brand-400" /> Implementation Roadmap & Architecture
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Phased engineering milestones, tailored technology stack, database schemas, and interactive task board.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {ideas.length > 0 && (
            <select
              value={selectedIdeaId || ''}
              onChange={(e) => setSelectedIdeaId(parseInt(e.target.value))}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              {ideas.map((i) => (
                <option key={i.id} value={i.id}>
                  Idea: {i.title}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={handleGenerate}
            disabled={generating || !selectedIdeaId}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50 shrink-0"
          >
            {generating ? (
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {roadmap ? 'Regenerate Roadmap' : 'Generate Technical Roadmap'}
          </button>
        </div>
      </div>

      {!roadmap ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <Milestone className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-300">No Roadmap Generated</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
            Click 'Generate Technical Roadmap' to build a complete phased development plan, API designs, and task tracker.
          </p>
          <button
            onClick={handleGenerate}
            disabled={!selectedIdeaId}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            Generate Roadmap
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Sub Navigation */}
          <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl self-start">
            <button
              onClick={() => setActiveTab('milestones')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'milestones' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Phased Milestones & MVP
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'tasks' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Interactive Task Tracker ({roadmap.task_breakdown?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'architecture' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tech Stack & DB Architecture
            </button>
          </div>

          {/* TAB 1: MILESTONES & MVP SCOPE */}
          {activeTab === 'milestones' && (
            <div className="space-y-6">
              {/* Objectives & Scope Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-brand-400">Project Objectives</h3>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {roadmap.objectives?.map((obj, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-brand-400 font-bold">•</span>
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Strict MVP Scope</h3>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {roadmap.mvp_scope?.map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-purple-400">Estimated Effort Ranges</h3>
                  <div className="space-y-1 text-xs text-slate-300 pt-1">
                    <p>Optimistic: <strong className="text-white">{roadmap.estimated_effort_ranges?.optimistic_weeks || 6} weeks</strong></p>
                    <p>Realistic: <strong className="text-white">{roadmap.estimated_effort_ranges?.realistic_weeks || 9} weeks</strong></p>
                    <p>Conservative: <strong className="text-white">{roadmap.estimated_effort_ranges?.conservative_weeks || 14} weeks</strong></p>
                  </div>
                </div>
              </div>

              {/* Phased Milestones Timeline */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-brand-400" /> Phased Execution Timeline
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {roadmap.phased_milestones?.map((phase, idx) => (
                    <div key={idx} className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl space-y-2 relative">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                          {phase.phase}
                        </span>
                        <span className="text-[10px] text-slate-400 font-medium">{phase.duration}</span>
                      </div>
                      <p className="text-xs text-slate-300 font-medium leading-relaxed">
                        {phase.deliverables}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: INTERACTIVE TASK TRACKER */}
          {activeTab === 'tasks' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-brand-400" /> Interactive Task Checklist
                  </h3>
                  <p className="text-xs text-slate-400">Click any task to toggle status between Todo, In Progress, and Done.</p>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-600" /> Todo</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> In Progress</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Done</span>
                </div>
              </div>

              <div className="divide-y divide-slate-800">
                {roadmap.task_breakdown?.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleToggleTaskStatus(task.id, task.status)}
                    className="py-3 px-3 rounded-xl hover:bg-slate-850 cursor-pointer flex items-center justify-between transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {task.status === 'done' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      ) : task.status === 'in_progress' ? (
                        <Clock className="w-5 h-5 text-amber-400 shrink-0 animate-spin" />
                      ) : (
                        <Square className="w-5 h-5 text-slate-600 shrink-0" />
                      )}
                      <div>
                        <span className={`text-xs font-semibold ${task.status === 'done' ? 'line-through text-slate-400' : 'text-slate-100'}`}>
                          {task.title}
                        </span>
                        <span className="text-[10px] text-slate-400 ml-2">({task.phase} • {task.estimated_days} days)</span>
                      </div>
                    </div>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full capitalize ${
                      task.status === 'done'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : task.status === 'in_progress'
                        ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: TECH STACK & DATABASE ARCHITECTURE */}
          {activeTab === 'architecture' && (
            <div className="space-y-6">
              {/* Stack Recommendation with Reasoning */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-brand-400" /> Recommended Technology Stack & Rationale
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(roadmap.recommended_tech_stack || {}).map(([layer, desc]) => (
                    <div key={layer} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-brand-400 tracking-wider">
                        {layer.replace('_', ' ')}
                      </span>
                      <p className="text-xs text-slate-200 leading-relaxed">{desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Database Entities & API Contracts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Database className="w-4 h-4 text-purple-400" /> Suggested Database Entities
                  </h3>
                  <div className="space-y-2 text-xs">
                    {roadmap.suggested_database_entities?.map((ent, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                        <span className="font-bold text-brand-400">{ent.name}</span>
                        <p className="text-slate-400 text-[11px] mt-0.5">{ent.purpose}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Server className="w-4 h-4 text-emerald-400" /> Key API Endpoints Spec
                  </h3>
                  <div className="space-y-2 text-xs">
                    {roadmap.api_design_endpoints?.map((ep, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-400">
                              {ep.method}
                            </span>
                            <span className="font-mono text-slate-200 text-[11px]">{ep.path}</span>
                          </div>
                          <p className="text-[10px] text-slate-400">{ep.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
