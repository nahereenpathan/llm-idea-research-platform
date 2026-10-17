import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { reportService } from '../services/reportService';
import { ideaService } from '../services/ideaService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  FileText,
  Plus,
  Trash2,
  Edit2,
  Save,
  Sparkles,
  FileCode,
  FileDown,
  RefreshCw,
  AlertCircle,
  Table,
  CheckCircle2,
  Calendar,
  Layers,
  BookOpen
} from 'lucide-react';

const REPORT_TEMPLATES = [
  { id: 'full_documentation', name: 'Comprehensive Research Whitepaper', desc: 'Complete 10-section dossier: problem, scores, papers, patents, gaps & roadmap' },
  { id: 'evaluation', name: 'Idea Evaluation & Viability Report', desc: 'Detailed 10-dimension mathematical viability & friction analysis' },
  { id: 'proposal', name: 'Academic & Venture Research Proposal', desc: 'Formal grant or institutional proposal with grounded literature' },
  { id: 'gap_report', name: 'Literature Gap & Prior Art Report', desc: 'Prior art review, author limitations, and open research questions' },
  { id: 'feasibility', name: 'Technical Feasibility & Architecture', desc: 'Database entities, API design specs, and recommended stack' },
  { id: 'implementation', name: 'Implementation & MVP Roadmap', desc: 'Phased milestones, task breakdown, dependencies, and assumptions' },
  { id: 'abstract', name: 'Academic Abstract & Scope Summary', desc: 'Structured academic abstract with methodology and outcomes' },
  { id: 'risk_assessment', name: 'Risk, Security & Audit Assessment', desc: 'Multi-tenant isolation, compliance, and technical risk mitigations' }
];

export default function ReportsPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('full_documentation');
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedMarkdown, setEditedMarkdown] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);

  const fetchReports = async () => {
    try {
      setErrorMessage(null);
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);

      const ideasList = await ideaService.listIdeas(projectId);
      setIdeas(ideasList);
      const selected = ideasList.find((i) => i.is_selected) || ideasList[0];
      if (selected) setSelectedIdeaId(selected.id);

      const list = await reportService.listReports(projectId);
      setReports(list);
      if (list.length > 0 && !activeReport) {
        selectReport(list[0]);
      }
    } catch (err) {
      console.error("Error loading reports:", err);
      setErrorMessage("Failed to load project reports.");
    } finally {
      setLoading(false);
    }
  };

  const selectReport = (rep) => {
    setActiveReport(rep);
    setEditedTitle(rep.title);
    setEditedMarkdown(rep.content_markdown);
    setIsEditing(false);
  };

  useEffect(() => {
    fetchReports();
  }, [projectId]);

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setGenerating(true);
    setErrorMessage(null);
    try {
      const newRep = await reportService.generateReport(projectId, {
        idea_id: selectedIdeaId,
        report_type: selectedTemplate
      });
      setShowNewModal(false);
      await fetchReports();
      selectReport(newRep);
    } catch (err) {
      console.error("Report generation failed:", err);
      setErrorMessage("Failed to generate research report. Please retry.");
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerateActive = async () => {
    if (!activeReport) return;
    setGenerating(true);
    setErrorMessage(null);
    try {
      const regenerated = await reportService.generateReport(projectId, {
        idea_id: activeReport.idea_id || selectedIdeaId,
        report_type: activeReport.report_type,
        title: activeReport.title
      });
      await fetchReports();
      selectReport(regenerated);
    } catch (err) {
      console.error("Failed to regenerate report:", err);
      setErrorMessage("Failed to refresh document. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!activeReport) return;
    try {
      const updated = await reportService.updateReport(activeReport.id, {
        title: editedTitle,
        content_markdown: editedMarkdown
      });
      setActiveReport(updated);
      setIsEditing(false);
      await fetchReports();
    } catch (err) {
      alert("Failed to save report changes.");
    }
  };

  const handleDelete = async (repId) => {
    if (window.confirm("Permanently delete this report?")) {
      try {
        await reportService.deleteReport(repId);
        const filtered = reports.filter(r => r.id !== repId);
        setReports(filtered);
        if (filtered.length > 0) selectReport(filtered[0]);
        else setActiveReport(null);
      } catch (err) {
        alert("Failed to delete report.");
      }
    }
  };

  const downloadExport = (format) => {
    if (!activeReport) return;
    const url = reportService.getExportUrl(activeReport.id, format);
    window.open(url, '_blank');
  };

  const downloadCsvScores = () => {
    const url = reportService.getCsvExportUrl(projectId);
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
        <span className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-medium">Loading documentation repository and export pipelines...</p>
      </div>
    );
  }

  const evidenceStatus = activeReport?.content_json?.evidence_status || 'moderate';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-400" /> Research Reports & Document Generator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Generate publication-grade whitepapers grounded in evaluations, literature, patents, and roadmaps with 1-click downloads.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={downloadCsvScores}
            title="Download structured CSV of all idea scores"
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 shadow-sm transition-all"
          >
            <Table className="w-4 h-4 text-emerald-400" /> Export Scores (CSV)
          </button>

          <button
            onClick={() => setShowNewModal(true)}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-md transition-all"
          >
            <Plus className="w-4 h-4" /> New Document
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => handleGenerate(null)}
            className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[11px] font-semibold flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}

      {/* Main Two Column View */}
      {reports.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-300">No Reports Generated Yet</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
            Select a template like Comprehensive Whitepaper, Research Proposal, or Feasibility Report to draft your first deliverable.
          </p>
          <button
            onClick={() => setShowNewModal(true)}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            Create Report Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-[640px]">
          {/* Reports Navigation Sidebar */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-1">
              Project Documents ({reports.length})
            </span>
            <div className="space-y-1.5 flex-1 overflow-y-auto">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  onClick={() => selectReport(rep)}
                  className={`p-3 rounded-xl cursor-pointer text-xs flex items-center justify-between group transition-all ${
                    activeReport?.id === rep.id
                      ? 'bg-brand-600/15 border border-brand-500/30 text-white font-semibold'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <div className="truncate pr-2">
                    <p className="truncate text-xs font-medium">{rep.title}</p>
                    <span className="text-[10px] text-slate-500 capitalize">
                      {rep.report_type.replace('_', ' ')}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(rep.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-opacity"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Report Viewer / Markdown Editor */}
          {activeReport && (
            <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-sm">
              {/* Document Action Bar */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex flex-wrap items-center justify-between gap-3">
                <div className="flex-1 min-w-[200px]">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      className="w-full px-2.5 py-1 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white font-bold focus:outline-none focus:border-brand-500"
                    />
                  ) : (
                    <h2 className="text-sm font-bold text-white truncate">{activeReport.title}</h2>
                  )}

                  <div className="flex flex-wrap items-center gap-2 mt-1 text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(activeReport.created_at).toLocaleDateString()}
                    </span>
                    <span>•</span>
                    <span
                      className={`px-2 py-0.2 rounded-full border capitalize ${
                        evidenceStatus === 'rich'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : evidenceStatus === 'moderate'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      }`}
                    >
                      {evidenceStatus} Evidence
                    </span>
                    {activeReport.content_json?.saved_papers_count !== undefined && (
                      <span>• {activeReport.content_json.saved_papers_count} papers cited</span>
                    )}
                  </div>
                </div>

                {/* Edit, Regenerate & Export Controls */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={handleRegenerateActive}
                    disabled={generating}
                    title="Regenerate this report with the latest database evidence"
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
                    {generating ? 'Regenerating...' : 'Regenerate'}
                  </button>

                  {isEditing ? (
                    <button
                      onClick={handleSaveEdit}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                    >
                      <Save className="w-3.5 h-3.5" /> Save Changes
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700"
                    >
                      <Edit2 className="w-3.5 h-3.5" /> Edit Markdown
                    </button>
                  )}

                  {/* Export Buttons */}
                  <div className="flex items-center gap-1 pl-2 border-l border-slate-800">
                    <button
                      onClick={() => downloadExport('pdf')}
                      title="Download PDF format"
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 border border-slate-700 transition-colors"
                    >
                      <FileDown className="w-3.5 h-3.5 text-red-400" /> PDF
                    </button>
                    <button
                      onClick={() => downloadExport('docx')}
                      title="Download Microsoft Word format"
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 border border-slate-700 transition-colors"
                    >
                      <FileDown className="w-3.5 h-3.5 text-blue-400" /> DOCX
                    </button>
                    <button
                      onClick={() => downloadExport('md')}
                      title="Download Markdown source"
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 border border-slate-700 transition-colors"
                    >
                      <FileCode className="w-3.5 h-3.5 text-purple-400" /> MD
                    </button>
                    <button
                      onClick={() => downloadExport('latex')}
                      title="Download LaTeX format"
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 border border-slate-700 transition-colors"
                    >
                      <FileDown className="w-3.5 h-3.5 text-emerald-400" /> TeX
                    </button>
                  </div>
                </div>
              </div>

              {/* Editor or Formatted Preview Area */}
              <div className="flex-1 p-6 overflow-y-auto">
                {isEditing ? (
                  <textarea
                    rows={22}
                    value={editedMarkdown}
                    onChange={(e) => setEditedMarkdown(e.target.value)}
                    className="w-full h-full p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-200 leading-relaxed focus:outline-none focus:border-brand-500"
                  />
                ) : (
                  <div className="prose prose-invert max-w-none text-xs text-slate-200 space-y-4 whitespace-pre-line leading-relaxed font-sans">
                    {activeReport.content_markdown}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generate Report Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="text-base font-bold text-white">Generate Structured Project Report</h2>
            <p className="text-xs text-slate-400">
              Select a deliverable template. Synthesizes evaluations, verified literature citations, and architecture specifications.
            </p>

            <form onSubmit={handleGenerate} className="space-y-4">
              {ideas.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Idea Candidate</label>
                  <select
                    value={selectedIdeaId || ''}
                    onChange={(e) => setSelectedIdeaId(parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    {ideas.map((i) => (
                      <option key={i.id} value={i.id}>{i.title}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">Select Template</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[260px] overflow-y-auto pr-1">
                  {REPORT_TEMPLATES.map((tmpl) => (
                    <div
                      key={tmpl.id}
                      onClick={() => setSelectedTemplate(tmpl.id)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        selectedTemplate === tmpl.id
                          ? 'bg-brand-600/15 border-brand-500/40 text-white'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <p className="text-xs font-semibold text-white">{tmpl.name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{tmpl.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md disabled:opacity-50 flex items-center gap-1.5"
                >
                  {generating ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      Drafting Document...
                    </>
                  ) : (
                    'Generate Document'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
