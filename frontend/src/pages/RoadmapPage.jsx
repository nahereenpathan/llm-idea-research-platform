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
  Database,
  Server,
  Code2,
  ShieldCheck,
  AlertCircle,
  Calendar,
  CheckSquare,
  Square,
  Edit2,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  Rocket
} from 'lucide-react';

const PRIORITY_BADGES = {
  high: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  low: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
};

export default function RoadmapPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('milestones'); // 'milestones', 'tasks', 'architecture', 'risks_assumptions'
  const [errorMessage, setErrorMessage] = useState(null);

  // Task inline editing state
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editFormData, setEditFormData] = useState({
    title: '',
    status: 'todo',
    priority: 'medium',
    estimated_days: 3,
  });
  const [savingTask, setSavingTask] = useState(false);

  // Task filtering
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchData = async () => {
    try {
      setErrorMessage(null);
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
      setErrorMessage("Failed to load implementation blueprint.");
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
    setErrorMessage(null);
    try {
      const res = await roadmapService.generateRoadmap(projectId, selectedIdeaId);
      setRoadmap(res);
    } catch (err) {
      console.error("Roadmap generation failed:", err);
      setErrorMessage("Failed to generate implementation roadmap.");
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleTaskStatus = async (taskId, currentStatus, e) => {
    e?.stopPropagation();
    const nextStatus = currentStatus === 'done' ? 'todo' : currentStatus === 'todo' ? 'in_progress' : 'done';
    try {
      const updated = await roadmapService.updateTaskStatus(projectId, taskId, nextStatus);
      setRoadmap(updated);
    } catch (err) {
      console.error("Failed to toggle status:", err);
      alert("Failed to update task status.");
    }
  };

  const startEditTask = (task, e) => {
    e.stopPropagation();
    setEditingTaskId(task.id);
    setEditFormData({
      title: task.title,
      status: task.status || 'todo',
      priority: task.priority || 'medium',
      estimated_days: task.estimated_days || 3,
    });
  };

  const saveEditTask = async (taskId, e) => {
    e?.stopPropagation();
    setSavingTask(true);
    try {
      const updated = await roadmapService.updateTaskDetails(projectId, taskId, editFormData);
      setRoadmap(updated);
      setEditingTaskId(null);
    } catch (err) {
      console.error("Failed to save task edits:", err);
      alert("Failed to save task modifications.");
    } finally {
      setSavingTask(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
        <span className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-medium">Synthesizing architectural specifications and milestones...</p>
      </div>
    );
  }

  const tasks = roadmap?.task_breakdown || [];
  const filteredTasks = tasks.filter((t) => {
    if (statusFilter === 'all') return true;
    return t.status === statusFilter;
  });

  const completedCount = tasks.filter((t) => t.status === 'done').length;
  const inProgressCount = tasks.filter((t) => t.status === 'in_progress').length;
  const todoCount = tasks.filter((t) => t.status === 'todo').length;

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

      {/* Error alert banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={handleGenerate}
            className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[11px] font-semibold flex items-center gap-1 transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}

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
          {/* Sub Navigation Strip */}
          <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl self-start overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab('milestones')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'milestones' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Phased Milestones & MVP Scope
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'tasks' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Interactive Task Board</span>
              <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-brand-300">
                {tasks.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'architecture' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tech Stack & Architecture Blueprint
            </button>
            <button
              onClick={() => setActiveTab('risks_assumptions')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'risks_assumptions' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Risks, Testing & Effort Assumptions
            </button>
          </div>

          {/* TAB 1: MILESTONES & MVP SCOPE */}
          {activeTab === 'milestones' && (
            <div className="space-y-6">
              {/* Objectives & Scope Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-brand-400 flex items-center gap-1.5">
                    <Rocket className="w-4 h-4" /> Strategic Objectives
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {roadmap.objectives?.map((obj, i) => (
                      <li key={i} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded-lg border border-slate-850">
                        <span className="text-brand-400 font-bold">•</span>
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Strict MVP Scope
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {roadmap.mvp_scope?.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded-lg border border-slate-850">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
                    <Clock className="w-4 h-4" /> Effort Forecast Ranges
                  </h3>
                  <div className="space-y-2.5 text-xs text-slate-300 pt-1">
                    <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-400">Optimistic Pace:</span>
                      <strong className="text-white font-mono">{roadmap.estimated_effort_ranges?.optimistic_weeks || 6} weeks</strong>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/50 border border-purple-500/30 flex items-center justify-between">
                      <span className="text-purple-300 font-medium">Realistic Target:</span>
                      <strong className="text-purple-300 font-mono text-sm">{roadmap.estimated_effort_ranges?.realistic_weeks || 9} weeks</strong>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-400">Conservative Buffer:</span>
                      <strong className="text-white font-mono">{roadmap.estimated_effort_ranges?.conservative_weeks || 14} weeks</strong>
                    </div>
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
                    <div key={idx} className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl space-y-2.5 relative">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                          {phase.phase}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">{phase.duration}</span>
                      </div>
                      <p className="text-xs text-slate-200 font-medium leading-relaxed">
                        {phase.deliverables}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: INTERACTIVE TASK BOARD & CHECKLIST */}
          {activeTab === 'tasks' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-brand-400" /> Interactive Task Management Board
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Update task status, edit priority, and adjust timeline estimates. Changes persist directly to PostgreSQL.
                  </p>
                </div>

                {/* Progress summary & Filter */}
                <div className="flex items-center gap-2 text-xs">
                  <button
                    onClick={() => setStatusFilter('all')}
                    className={`px-2.5 py-1 rounded-lg border transition-colors ${
                      statusFilter === 'all'
                        ? 'bg-brand-600 text-white border-brand-500'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    All ({tasks.length})
                  </button>
                  <button
                    onClick={() => setStatusFilter('todo')}
                    className={`px-2.5 py-1 rounded-lg border transition-colors flex items-center gap-1.5 ${
                      statusFilter === 'todo'
                        ? 'bg-slate-800 text-white border-slate-600'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <span className="w-2 h-2 rounded-full bg-slate-500" /> Todo ({todoCount})
                  </button>
                  <button
                    onClick={() => setStatusFilter('in_progress')}
                    className={`px-2.5 py-1 rounded-lg border transition-colors flex items-center gap-1.5 ${
                      statusFilter === 'in_progress'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <span className="w-2 h-2 rounded-full bg-amber-400" /> In Progress ({inProgressCount})
                  </button>
                  <button
                    onClick={() => setStatusFilter('done')}
                    className={`px-2.5 py-1 rounded-lg border transition-colors flex items-center gap-1.5 ${
                      statusFilter === 'done'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <span className="w-2 h-2 rounded-full bg-emerald-400" /> Done ({completedCount})
                  </button>
                </div>
              </div>

              {/* Tasks List */}
              <div className="divide-y divide-slate-800/80">
                {filteredTasks.length === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-xs">No tasks match the selected filter.</div>
                ) : (
                  filteredTasks.map((task) => (
                    <div
                      key={task.id}
                      className="py-3.5 px-3 rounded-xl hover:bg-slate-850/60 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3"
                    >
                      {editingTaskId === task.id ? (
                        /* Inline Edit Mode */
                        <div className="flex-1 space-y-3 p-3 bg-slate-950 rounded-xl border border-brand-500/40">
                          <div className="space-y-1">
                            <label className="text-[10px] text-slate-400 uppercase font-semibold">Task Title</label>
                            <input
                              type="text"
                              value={editFormData.title}
                              onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500"
                            />
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                              <label className="text-[10px] text-slate-400 uppercase font-semibold">Status</label>
                              <select
                                value={editFormData.status}
                                onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
                              >
                                <option value="todo">Todo</option>
                                <option value="in_progress">In Progress</option>
                                <option value="done">Done</option>
                              </select>
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 uppercase font-semibold">Priority</label>
                              <select
                                value={editFormData.priority}
                                onChange={(e) => setEditFormData({ ...editFormData, priority: e.target.value })}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
                              >
                                <option value="high">High Priority</option>
                                <option value="medium">Medium Priority</option>
                                <option value="low">Low Priority</option>
                              </select>
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 uppercase font-semibold">Estimated Days</label>
                              <input
                                type="number"
                                min="1"
                                max="90"
                                value={editFormData.estimated_days}
                                onChange={(e) => setEditFormData({ ...editFormData, estimated_days: parseInt(e.target.value) || 1 })}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
                              />
                            </div>
                          </div>
                          <div className="flex items-center justify-end gap-2 pt-1">
                            <button
                              onClick={() => setEditingTaskId(null)}
                              className="px-3 py-1 rounded bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={(e) => saveEditTask(task.id, e)}
                              disabled={savingTask}
                              className="px-3 py-1 rounded bg-brand-600 text-white text-xs font-semibold hover:bg-brand-500 flex items-center gap-1"
                            >
                              {savingTask ? 'Saving...' : 'Save Changes'}
                            </button>
                          </div>
                        </div>
                      ) : (
                        /* Normal View Mode */
                        <>
                          <div className="flex items-start gap-3 flex-1">
                            <button
                              onClick={(e) => handleToggleTaskStatus(task.id, task.status, e)}
                              className="mt-0.5 shrink-0 focus:outline-none"
                              title="Toggle status"
                            >
                              {task.status === 'done' ? (
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                              ) : task.status === 'in_progress' ? (
                                <Clock className="w-5 h-5 text-amber-400 animate-pulse" />
                              ) : (
                                <Square className="w-5 h-5 text-slate-600 hover:text-slate-400" />
                              )}
                            </button>

                            <div className="space-y-1">
                              <span
                                className={`text-xs font-semibold block ${
                                  task.status === 'done' ? 'line-through text-slate-500' : 'text-slate-100'
                                }`}
                              >
                                {task.title}
                              </span>

                              <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
                                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                  {task.phase}
                                </span>
                                <span>•</span>
                                <span>{task.estimated_days} days est.</span>

                                {task.dependencies && task.dependencies.length > 0 && (
                                  <>
                                    <span>•</span>
                                    <span className="text-slate-400">
                                      Deps: <span className="text-brand-300">{task.dependencies.join(', ')}</span>
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2.5 self-end md:self-center">
                            {/* Priority badge */}
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize border ${
                                PRIORITY_BADGES[task.priority] || PRIORITY_BADGES.medium
                              }`}
                            >
                              {task.priority || 'medium'}
                            </span>

                            {/* Status badge */}
                            <span
                              className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full capitalize border ${
                                task.status === 'done'
                                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                                  : task.status === 'in_progress'
                                  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                                  : 'bg-slate-800 text-slate-400 border-slate-700'
                              }`}
                            >
                              {task.status.replace('_', ' ')}
                            </span>

                            {/* Edit button */}
                            <button
                              onClick={(e) => startEditTask(task, e)}
                              title="Edit task parameters"
                              className="p-1 text-slate-500 hover:text-brand-400 transition-colors"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: TECH STACK & DATABASE ARCHITECTURE */}
          {activeTab === 'architecture' && (
            <div className="space-y-6">
              {/* Stack Recommendation with Reasoning */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-brand-400" /> Recommended Technology Stack & Architecture Rationale
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
                      <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                        <span className="font-bold text-brand-400">{ent.name}</span>
                        <p className="text-slate-300 text-[11px] mt-1">{ent.purpose}</p>
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

          {/* TAB 4: RISKS, TESTING & EFFORT ASSUMPTIONS */}
          {activeTab === 'risks_assumptions' && (
            <div className="space-y-6">
              {/* Effort Estimate Assumptions */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-brand-400" /> Assumptions Behind Effort & Timeline Estimates
                </h3>
                <p className="text-xs text-slate-400">
                  Engineering forecasts depend on team composition, existing code reusable modules, and third-party API stability:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {roadmap.effort_estimate_assumptions?.map((assump, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-950/70 border border-slate-850 text-xs text-slate-300 leading-relaxed flex items-start gap-2">
                      <span className="text-brand-400 font-bold">•</span>
                      <span>{assump}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risks & Mitigations */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" /> Architectural Risks & Mitigations
                </h3>
                <div className="space-y-2.5">
                  {roadmap.risks_and_mitigations?.map((item, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-rose-400 tracking-wider block mb-1">Identified Risk</span>
                        <p className="text-slate-200">{item.risk}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider block mb-1">Recommended Mitigation</span>
                        <p className="text-slate-300">{item.mitigation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Testing & Deployment Strategy */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" /> Testing & Quality Assurance Plan
                  </h3>
                  <div className="space-y-2 text-xs">
                    {roadmap.testing_strategy?.map((item, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-2">
                        <span className="text-cyan-400 font-bold">•</span>
                        <span className="text-slate-300">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Rocket className="w-4 h-4 text-indigo-400" /> Deployment & CI/CD Blueprint
                  </h3>
                  <div className="space-y-2 text-xs">
                    {roadmap.deployment_strategy?.map((item, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-2">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span className="text-slate-300">{item}</span>
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
