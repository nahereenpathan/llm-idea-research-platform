import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  FolderKanban,
  Plus,
  ArrowRight,
  Trash2,
  Edit2,
  Download,
  AlertCircle,
  Tag,
  CheckCircle2,
  Calendar
} from 'lucide-react';

export default function Projects() {
  const { projects, loadProjects, setActiveProject } = useProject();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [title, setTitle] = useState('');
  const [domain, setDomain] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleCreateOrUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (editingProject) {
        await projectService.updateProject(editingProject.id, { title, domain, description });
      } else {
        const newProj = await projectService.createProject({ title, domain, description });
        setActiveProject(newProj);
      }
      setShowCreateModal(false);
      setEditingProject(null);
      setTitle('');
      setDomain('');
      setDescription('');
      await loadProjects();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save project.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, title) => {
    if (window.confirm(`Are you sure you want to permanently delete project "${title}" and all its submitted ideas, reports, and presentations?`)) {
      try {
        await projectService.deleteProject(id);
        await loadProjects();
      } catch (err) {
        alert('Failed to delete project.');
      }
    }
  };

  const handleExportData = async (id, title) => {
    try {
      const data = await projectService.exportAllProjectData(id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_full_archive.json`;
      a.click();
    } catch (err) {
      alert('Failed to export project archive.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-brand-400" /> Research Projects
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Organize multi-idea comparison experiments, patent notes, literature libraries, and presentations.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingProject(null);
            setTitle('');
            setDomain('');
            setDescription('');
            setShowCreateModal(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-600/20 transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <FolderKanban className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No Projects Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            Get started by creating your first research project. You can compare up to 3 candidate ideas inside each project.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            <Plus className="w-4 h-4" /> Create Project Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all group shadow-sm hover:shadow-black/30"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-slate-800 text-brand-400 border border-slate-700 flex items-center gap-1">
                    <Tag className="w-3 h-3" /> {proj.domain || 'General Domain'}
                  </span>
                  <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleExportData(proj.id, proj.title)}
                      title="Export full project JSON archive"
                      className="p-1 rounded text-slate-400 hover:text-brand-400 hover:bg-slate-800"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        setEditingProject(proj);
                        setTitle(proj.title);
                        setDomain(proj.domain || '');
                        setDescription(proj.description || '');
                        setShowCreateModal(true);
                      }}
                      title="Edit project details"
                      className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(proj.id, proj.title)}
                      title="Delete project"
                      className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="text-base font-bold text-white group-hover:text-brand-400 transition-colors line-clamp-1">
                  {proj.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  {proj.description || 'No description provided.'}
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="font-semibold text-slate-200">{proj.idea_count || 0}/3</span> ideas
                </div>
                <button
                  onClick={() => {
                    setActiveProject(proj);
                    navigate(`/projects/${proj.id}/compare`);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  Open Workspace <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-1">
              {editingProject ? 'Edit Project' : 'Create New Project Workspace'}
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter your project parameters to start comparing candidate ideas.
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateOrUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Project Title *</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., AI Clinical Trial Matching Engine"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Domain / Industry</label>
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="e.g., Biotech & Healthcare, Clean Energy, Fintech"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description & Scope</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summarize the core innovation challenge and constraints..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md disabled:opacity-50"
                >
                  {loading ? 'Saving...' : (editingProject ? 'Save Changes' : 'Create Project')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
