import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { gapService } from '../services/gapService';
import { ideaService } from '../services/ideaService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Split,
  Sparkles,
  ExternalLink,
  BookOpen,
  HelpCircle,
  FlaskConical,
  AlertCircle,
  Layers,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  FileText,
  RefreshCw
} from 'lucide-react';

export default function GapAnalysisPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const fetchData = async () => {
    try {
      setErrorMessage(null);
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);

      const ideasList = await ideaService.listIdeas(projectId);
      setIdeas(ideasList);

      const active = ideasList.find((i) => i.is_selected) || ideasList[0];
      if (active) setSelectedIdeaId(active.id);

      const analyses = await gapService.getGapAnalyses(projectId);
      if (analyses.length > 0) {
        setGapAnalysis(analyses[0]);
      }
    } catch (err) {
      console.error("Error loading gap analysis:", err);
      setErrorMessage("Failed to load project or literature analysis data.");
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
      const res = await gapService.generateGapAnalysis(projectId, selectedIdeaId);
      setGapAnalysis(res);
    } catch (err) {
      console.error("Gap generation failed:", err);
      setErrorMessage("Failed to generate research gap analysis. Please verify your connection or try again.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
        <span className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-medium">Scanning saved academic literature and patent index...</p>
      </div>
    );
  }

  const evidenceStatus = gapAnalysis?.evidence_status || 'moderate';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Split className="w-5 h-5 text-brand-400" /> Literature & Research Gap Analysis
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Synthesize existing academic findings, author limitations, and potential unexplored research questions.
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
            {gapAnalysis ? 'Regenerate Gap Report' : 'Synthesize Research Gaps'}
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

      {/* Evidence Density & Epistemic Disclaimer Banner */}
      {gapAnalysis && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <div className="flex items-center gap-2.5">
              <span className="font-semibold text-slate-300">Evidence Grounding Status:</span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold capitalize flex items-center gap-1 border ${
                  evidenceStatus === 'rich'
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : evidenceStatus === 'moderate'
                    ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                    : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                }`}
              >
                {evidenceStatus === 'rich' ? (
                  <CheckCircle2 className="w-3 h-3" />
                ) : (
                  <AlertCircle className="w-3 h-3" />
                )}
                {evidenceStatus} Evidence ({gapAnalysis.citations?.length || 0} Grounded Records)
              </span>
            </div>

            <Link
              to={`/projects/${projectId}/research`}
              className="text-brand-400 hover:text-brand-300 text-[11px] font-medium flex items-center gap-1"
            >
              Open Research Workspace to Save Papers <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {/* Limitation notice when evidence is limited */}
          {gapAnalysis.evidence_limitation_notice && (
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
              <div className="leading-relaxed">
                <strong className="font-semibold text-amber-200">Limited Evidence Notice: </strong>
                {gapAnalysis.evidence_limitation_notice}
              </div>
            </div>
          )}
        </div>
      )}

      {/* General epistemic method notice */}
      <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400 leading-relaxed">
        <strong className="text-slate-300">Methodological Standard:</strong> Identified research gaps represent promising exploratory directions based on accessible literature abstracts and patent repositories. They are not guaranteed absolute novelty claims.
      </div>

      {!gapAnalysis ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-300">No Research Gap Report Generated</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
            Click 'Synthesize Research Gaps' to scan saved literature, map author limitations, and generate investigation questions.
          </p>
          <button
            onClick={handleGenerate}
            disabled={!selectedIdeaId}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            Generate Gap Report
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Section Grid: Existing Approaches & Common Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" /> Existing Approaches in Prior Work
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.existing_approaches?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-400" /> Common Empirical Findings
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.common_findings?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Conflicting Findings & Limitations in Literature */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400" /> Conflicting or Contested Findings
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.conflicting_findings?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400" /> Limitations Reported by Authors
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.limitations_in_prior_work?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Identified Research Gaps (Highlighted) */}
          <div className="bg-gradient-to-br from-slate-900 to-navy-900 border border-brand-500/30 rounded-2xl p-6 space-y-3 shadow-lg">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Split className="w-5 h-5 text-brand-400" /> Key Identified Research Gaps
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {gapAnalysis.identified_gaps?.map((gap, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/70 border border-brand-500/20 text-xs text-slate-200 leading-relaxed flex items-start gap-2.5">
                  <span className="text-brand-400 font-bold font-mono">0{idx + 1}.</span>
                  <span>{gap}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Suggested Research Questions & Proposed Evaluation Methods */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-purple-400" /> Suggested Research Questions
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.suggested_research_questions?.map((item, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 leading-relaxed font-medium text-slate-200">
                    "{item}"
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-cyan-400" /> Proposed Evaluation Experiments
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.proposed_evaluation_methods?.map((item, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 leading-relaxed text-slate-300">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Verified Supporting Citations */}
          {gapAnalysis.citations && gapAnalysis.citations.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-brand-400" /> Supporting Scholarly & Patent Citations ({gapAnalysis.citations.length})
                </h3>
                <span className="text-[10px] text-slate-400">All links point to verified source records</span>
              </div>
              <div className="divide-y divide-slate-800 text-xs">
                {gapAnalysis.citations.map((cite, idx) => (
                  <div key={idx} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="font-semibold text-slate-200">{cite.title}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 pl-5.5">
                        {cite.relevance_note} {cite.external_id ? `• Record ID: ${cite.external_id}` : ''}
                      </p>
                    </div>
                    {cite.source_url ? (
                      <a
                        href={cite.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-400 hover:underline flex items-center gap-1 text-[11px] shrink-0 self-start sm:self-center"
                      >
                        View Source <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-[10px] text-slate-500 italic shrink-0">Metadata indexed</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
